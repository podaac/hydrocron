"""Post-ingest verification — reads SOS file, queries DB, reports discrepancies."""
import csv
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.db_client import SosDbClient
from SOS.sos_ingest.helpers import find_db_row, parse_db_times
from SOS.sos_ingest.models import ScanSummary
from SOS.sos_ingest.reader import ALGORITHM_CONFIG, get_reach_count, read_sos_file
from SOS.sos_ingest.time_matcher import find_closest_time
from SOS.sos_ingest.ui import IngestUI

logger = logging.getLogger(__name__)

SCAN_CSV_COLUMNS = [
    "reach_id", "sos_time", "matched_range_start_time", "column",
    "status", "expected_value", "actual_value",
]


def scan(config: IngestConfig) -> ScanSummary:
    """Post-ingest verification. Reports discrepancies between SOS file and DB."""
    ui = IngestUI()
    sos_filename = os.path.basename(config.sos_file)
    db_client = SosDbClient(config.table_name, dry_run=True, aws_profile=config.aws_profile)

    # Determine which algorithm columns to check
    algo_defs = ALGORITHM_CONFIG if "all" in config.algorithms else [a for a in ALGORITHM_CONFIG if a.name in config.algorithms]
    algo_column_map = {a.name: a.column_name for a in algo_defs}

    # Read SOS file with progress bar
    total_reaches_in_file = get_reach_count(config.sos_file)
    progress = ui.create_reading_progress(total_reaches_in_file)
    with progress:
        task_id = list(progress.task_ids)[0]
        reach_data, _missing_counts = read_sos_file(
            config.sos_file, config.algorithms,
            on_reach_progress=lambda n: progress.advance(task_id, n)
        )

    # Filter to range
    all_reach_ids = list(reach_data.keys())
    if config.start_reach_id:
        all_reach_ids = [rid for rid in all_reach_ids if int(rid) >= int(config.start_reach_id)]
    if config.stop_reach_id:
        all_reach_ids = [rid for rid in all_reach_ids if int(rid) <= int(config.stop_reach_id)]

    # Set up scan CSV
    os.makedirs(config.output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    base = os.path.splitext(sos_filename)[0]
    scan_path = os.path.join(config.output_dir, f"{base}_scan_{timestamp}.csv")
    scan_file = open(scan_path, "w", newline="")
    writer = csv.DictWriter(scan_file, fieldnames=SCAN_CSV_COLUMNS)
    writer.writeheader()

    discrepancies: list[dict] = []
    ok = 0
    no_rows = 0
    no_time_match = 0
    missing_column = 0
    value_mismatch = 0
    total_time_steps = 0

    # Scan progress
    total_steps = sum(
        len(set(rec.sos_time_seconds for rec in reach_data[rid].records))
        for rid in all_reach_ids
    )
    scan_progress = ui.create_scan_progress(total_steps)

    with scan_progress:
        task_id = list(scan_progress.task_ids)[0]

        for reach_id in all_reach_ids:
            rds = reach_data[reach_id]

            # Group by time step
            time_groups: dict[float, list] = defaultdict(list)
            for rec in rds.records:
                time_groups[rec.sos_time_seconds].append(rec)

            try:
                rows = db_client.query_reach(reach_id)
            except Exception as e:
                logger.error("Failed to query reach %s: %s", reach_id, e)
                no_rows += 1
                for t_seconds in time_groups:
                    total_time_steps += 1
                    scan_progress.advance(task_id, 1)
                continue

            if not rows:
                no_rows += 1
                for t_seconds, recs in time_groups.items():
                    row_data = {
                        "reach_id": reach_id,
                        "sos_time": recs[0].sos_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "matched_range_start_time": "",
                        "column": "",
                        "status": "no_rows",
                        "expected_value": "",
                        "actual_value": "",
                    }
                    writer.writerow(row_data)
                    discrepancies.append(row_data)
                    total_time_steps += 1
                    scan_progress.advance(task_id, 1)
                continue

            db_times = parse_db_times(rows)

            for t_seconds in sorted(time_groups.keys()):
                recs = time_groups[t_seconds]
                sos_dt = recs[0].sos_datetime
                total_time_steps += 1

                matched_time, delta, status = find_closest_time(sos_dt, db_times, config.time_tolerance_seconds)

                if status != "matched":
                    csv_status = "no_time_match" if status == "no_match" else status
                    row_data = {
                        "reach_id": reach_id,
                        "sos_time": sos_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "matched_range_start_time": "",
                        "column": "",
                        "status": csv_status,
                        "expected_value": "",
                        "actual_value": "",
                    }
                    writer.writerow(row_data)
                    discrepancies.append(row_data)
                    no_time_match += 1
                    scan_progress.advance(task_id, 1)
                    continue

                db_row = find_db_row(rows, matched_time)

                # Check each algorithm column
                step_ok = True
                for rec in recs:
                    col = algo_column_map.get(rec.algorithm)
                    if not col:
                        continue
                    expected_val = str(float(rec.discharge_value))
                    actual_val = db_row.get(col, "") if db_row else ""

                    if not actual_val:
                        row_data = {
                            "reach_id": reach_id,
                            "sos_time": sos_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "matched_range_start_time": matched_time,
                            "column": col,
                            "status": "missing_column",
                            "expected_value": expected_val,
                            "actual_value": "",
                        }
                        writer.writerow(row_data)
                        discrepancies.append(row_data)
                        missing_column += 1
                        step_ok = False
                    elif actual_val != expected_val:
                        row_data = {
                            "reach_id": reach_id,
                            "sos_time": sos_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "matched_range_start_time": matched_time,
                            "column": col,
                            "status": "value_mismatch",
                            "expected_value": expected_val,
                            "actual_value": actual_val,
                        }
                        writer.writerow(row_data)
                        discrepancies.append(row_data)
                        value_mismatch += 1
                        step_ok = False

                if step_ok:
                    ok += 1

                scan_progress.advance(task_id, 1)

    scan_file.close()

    summary = ScanSummary(
        total_reaches=len(all_reach_ids),
        total_time_steps=total_time_steps,
        ok=ok,
        no_rows=no_rows,
        no_time_match=no_time_match,
        missing_column=missing_column,
        value_mismatch=value_mismatch,
    )

    ui.show_scan_results(summary, config, scan_path, discrepancies)

    return summary
