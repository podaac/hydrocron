"""Main orchestration loop for SOS ingest."""
import logging
import os
import signal
from collections import defaultdict
from datetime import datetime, timezone

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.db_client import SosDbClient
from SOS.sos_ingest.error_logger import IngestErrorLogger
from SOS.sos_ingest.helpers import find_db_row, parse_db_times
from SOS.sos_ingest.models import ProcessingSummary, ReachDischargeSet
from SOS.sos_ingest.reader import ALGORITHM_CONFIG, get_reach_count, read_sos_file
from SOS.sos_ingest.time_matcher import find_closest_time
from SOS.sos_ingest.ui import IngestUI

logger = logging.getLogger(__name__)

shutdown_requested = False


def _handle_sigint(signum, frame):
    global shutdown_requested
    if shutdown_requested:
        raise KeyboardInterrupt
    shutdown_requested = True
    logger.warning("Shutting down after current reach completes...")


def _group_by_time(rds: ReachDischargeSet) -> dict[float, list]:
    """Group discharge records by sos_time_seconds."""
    groups: dict[float, list] = defaultdict(list)
    for rec in rds.records:
        groups[rec.sos_time_seconds].append(rec)
    return dict(sorted(groups.items()))


def _build_column_updates(records: list) -> dict[str, str]:
    """Build the column_updates dict from all algorithm records at one time step."""
    algo_column_map = {a.name: a.column_name for a in ALGORITHM_CONFIG}
    updates: dict[str, str] = {}
    for rec in records:
        col = algo_column_map.get(rec.algorithm)
        if col:
            updates[col] = str(float(rec.discharge_value))
    return updates


def _row_already_has_values(db_row: dict | None, column_updates: dict[str, str]) -> bool:
    """Check if the DB row already has all SOS columns with the same values."""
    if db_row is None:
        return False
    for col, val in column_updates.items():
        if db_row.get(col) != val:
            return False
    return True


def _validate_config(config: IngestConfig) -> None:
    """Validate config upfront — abort with clear message on fatal issues."""
    if not os.path.isfile(config.sos_file):
        raise SystemExit(f"ERROR: SOS file not found: {config.sos_file}")
    if not os.access(config.sos_file, os.R_OK):
        raise SystemExit(f"ERROR: SOS file not readable: {config.sos_file}")
    os.makedirs(config.output_dir, exist_ok=True)
    if not os.access(config.output_dir, os.W_OK):
        raise SystemExit(f"ERROR: Output directory not writable: {config.output_dir}")


def run(config: IngestConfig) -> ProcessingSummary:
    """Main entry point. Processes one SOS file against the DynamoDB table."""
    _validate_config(config)

    global shutdown_requested
    shutdown_requested = False

    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _handle_sigint)

    ui = IngestUI()
    sos_filename = os.path.basename(config.sos_file)
    error_logger = IngestErrorLogger(config.output_dir, sos_filename, table_name=config.table_name)
    db_client = SosDbClient(config.table_name, config.dry_run, config.aws_profile)

    start_time = datetime.now(timezone.utc)

    # Read SOS file with progress bar
    total_reaches = get_reach_count(config.sos_file)
    progress = ui.create_reading_progress(total_reaches)
    with progress:
        task_id = list(progress.task_ids)[0]
        reach_data, missing_time_counts = read_sos_file(
            config.sos_file, config.algorithms,
            on_reach_progress=lambda n: progress.advance(task_id, n)
        )

    # Determine processing range
    all_reach_ids = list(reach_data.keys())
    total_in_file = len(all_reach_ids)

    if config.start_reach_id:
        all_reach_ids = [rid for rid in all_reach_ids if int(rid) >= int(config.start_reach_id)]
    if config.stop_reach_id:
        all_reach_ids = [rid for rid in all_reach_ids if int(rid) <= int(config.stop_reach_id)]

    reaches_to_process = len(all_reach_ids)
    reaches_skipped = total_in_file - reaches_to_process
    timesteps_to_process = sum(len(_group_by_time(reach_data[rid])) for rid in all_reach_ids)

    # Pre-flight summary and confirmation
    if not ui.show_preflight_summary(config, reach_data, reaches_to_process, timesteps_to_process, missing_time_counts):
        signal.signal(signal.SIGINT, original_handler)
        return ProcessingSummary(
            total_reaches=total_in_file, reaches_processed=0, reaches_skipped=reaches_skipped,
            total_time_steps=0,
            matched=0, updated=0, no_match=0, no_rows=0, ambiguous_match=0,
            skipped_unchanged=0, write_errors=0, dry_run=config.dry_run,
            start_time=start_time, end_time=datetime.now(timezone.utc),
        )

    # Processing loop
    matched = 0
    updated = 0
    no_match = 0
    no_rows = 0
    ambiguous_match = 0
    skipped_unchanged = 0
    write_errors = 0
    last_reach_id = None
    steps_processed = 0

    progress = ui.create_progress_bar(timesteps_to_process)
    with progress:
        task_id = list(progress.task_ids)[0]

        for reach_idx, reach_id in enumerate(all_reach_ids):
            if shutdown_requested:
                break

            progress.update(task_id, status=f"Current reach: {reach_id} (reach {reach_idx + 1:,} of {reaches_to_process:,}) | Write errors: {write_errors}")

            try:
                rds = reach_data[reach_id]
                time_groups = _group_by_time(rds)

                rows = db_client.query_reach(reach_id)

                if not rows:
                    no_rows += 1
                    for t_seconds, recs in time_groups.items():
                        error_logger.log(reach_id, recs[0].sos_datetime, t_seconds, None, None, "no_rows")
                        steps_processed += 1
                        progress.advance(task_id, 1)
                    error_logger.flush()
                    last_reach_id = reach_id
                    continue

                db_times = parse_db_times(rows)

                for t_seconds, recs in time_groups.items():
                    sos_dt = recs[0].sos_datetime
                    matched_time, delta, status = find_closest_time(sos_dt, db_times, config.time_tolerance_seconds)

                    if status == "no_match":
                        error_logger.log(reach_id, sos_dt, t_seconds, None, delta, "no_match")
                        no_match += 1
                        steps_processed += 1
                        progress.advance(task_id, 1)
                        continue

                    if status == "ambiguous_match":
                        error_logger.log(reach_id, sos_dt, t_seconds, None, delta, "ambiguous_match")
                        ambiguous_match += 1
                        steps_processed += 1
                        progress.advance(task_id, 1)
                        continue

                    column_updates = _build_column_updates(recs)
                    matched += 1

                    db_row = find_db_row(rows, matched_time)
                    if _row_already_has_values(db_row, column_updates):
                        skipped_unchanged += 1
                        steps_processed += 1
                        progress.advance(task_id, 1)
                        continue

                    if config.dry_run:
                        steps_processed += 1
                        progress.advance(task_id, 1)
                        continue

                    success = db_client.update_row(reach_id, matched_time, column_updates)
                    if success:
                        updated += 1
                    else:
                        error_logger.log(reach_id, sos_dt, t_seconds, matched_time, delta, "write_error")
                        write_errors += 1

                    steps_processed += 1
                    progress.advance(task_id, 1)

            except Exception as e:
                logger.error("Error processing reach %s: %s", reach_id, e)
                write_errors += 1

            error_logger.flush()
            last_reach_id = reach_id

    end_time = datetime.now(timezone.utc)
    signal.signal(signal.SIGINT, original_handler)

    summary = ProcessingSummary(
        total_reaches=total_in_file,
        reaches_processed=reaches_to_process if not shutdown_requested else (all_reach_ids.index(last_reach_id) + 1 if last_reach_id and last_reach_id in all_reach_ids else 0),
        reaches_skipped=reaches_skipped,
        total_time_steps=steps_processed,
        matched=matched,
        updated=updated,
        no_match=no_match,
        no_rows=no_rows,
        ambiguous_match=ambiguous_match,
        skipped_unchanged=skipped_unchanged,
        write_errors=write_errors,
        dry_run=config.dry_run,
        last_reach_id=last_reach_id,
        start_time=start_time,
        end_time=end_time,
    )

    error_logger.write_summary(summary, config)
    error_logger.close()
    ui.show_completion_summary(summary, error_logger.error_path, error_logger.summary_path)

    return summary
