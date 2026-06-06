"""SOS NetCDF file reader — extracts discharge data grouped by reach_id."""
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import numpy as np
from netCDF4 import Dataset

from SOS.sos_ingest.models import AlgorithmDef, DischargeRecord, ReachDischargeSet

logger = logging.getLogger(__name__)

SOS_EPOCH = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
MISSING_TIME_VALUE = -999999999999.0

ALGORITHM_CONFIG = [
    AlgorithmDef(name="consensus", group="consensus", variable="consensus_q",
                 missing_source="self", column_name="sos_consensus_q"),
    AlgorithmDef(name="metroman", group="metroman", variable="allq",
                 missing_source="consensus", column_name="sos_metroman_q"),
    AlgorithmDef(name="momma", group="momma", variable="Q",
                 missing_source="self", column_name="sos_momma_q"),
    AlgorithmDef(name="sic4dvar", group="sic4dvar", variable="Q_da",
                 missing_source="self", column_name="sos_sic4dvar_q"),
    AlgorithmDef(name="sad", group="sad", variable="Qa",
                 missing_source="self", column_name="sos_sad_q"),
    AlgorithmDef(name="hivdi", group="hivdi", variable="Q",
                 missing_source="consensus", column_name="sos_hivdi_q"),
    AlgorithmDef(name="lakeflow", group="lakeflow", variable="q_lakeflow",
                 missing_source="self", column_name="sos_lakeflow_q"),
]


def sos_seconds_to_datetime(seconds: float) -> datetime:
    """Convert seconds since 2000-01-01 to UTC datetime."""
    return SOS_EPOCH + timedelta(seconds=seconds)


def get_reach_count(filepath: str) -> int:
    """Quick read of reaches/reach_id array to get total reach count."""
    ds = Dataset(filepath, "r")
    try:
        count = len(ds["reaches"]["reach_id"])
    finally:
        ds.close()
    return count


def _get_algorithms(requested: list[str]) -> list[AlgorithmDef]:
    """Filter ALGORITHM_CONFIG to only the requested algorithms."""
    if "all" in requested:
        return ALGORITHM_CONFIG
    return [a for a in ALGORITHM_CONFIG if a.name in requested]


def _read_lakeflow(
    ds: Dataset,
    reach_ids: np.ndarray,
    reach_data: dict[str, ReachDischargeSet],
    missing_time_counts: dict[str, int],
    on_reach_progress: Callable[[int], None] | None,
) -> None:
    """Read lakeflow discharge — fixed 2D array with shared 1D time axis. Runs last to match times."""
    try:
        lakeflow_grp = ds["lakeflow"]
        discharge_var = lakeflow_grp["q_lakeflow"]
        time_var = lakeflow_grp["lakeflow_date"]
    except (IndexError, KeyError):
        logger.warning("Algorithm group 'lakeflow/q_lakeflow' not found in file, skipping")
        return

    # Read full arrays upfront
    all_discharge = np.array(discharge_var[:], dtype=np.float64)
    lakeflow_times = np.array(time_var[:], dtype=np.float64)
    fill_value = float(discharge_var._FillValue)
    time_fill = float(time_var._FillValue)

    # Build valid mask: not fill, not NaN
    valid_mask = np.isfinite(all_discharge) & (all_discharge != fill_value)

    num_reaches = all_discharge.shape[0]

    # Pre-compute lakeflow datetime strings for the shared time axis
    lakeflow_datetimes: list[datetime | None] = []
    for t in lakeflow_times:
        if t == time_fill or t == 0.0 or np.isnan(t):
            lakeflow_datetimes.append(None)
        else:
            lakeflow_datetimes.append(sos_seconds_to_datetime(float(t)))

    for reach_idx in range(num_reaches):
        if not np.any(valid_mask[reach_idx]):
            continue

        reach_id = str(int(reach_ids[reach_idx]))

        # Build a date→time lookup from existing records for this reach
        existing_times_by_date: dict[str, float] = {}
        if reach_id in reach_data:
            for rec in reach_data[reach_id].records:
                date_key = rec.sos_datetime.strftime("%Y-%m-%d")
                if date_key not in existing_times_by_date:
                    existing_times_by_date[date_key] = rec.sos_time_seconds

        discharge_row = all_discharge[reach_idx]
        row_mask = valid_mask[reach_idx]

        new_records: list[DischargeRecord] = []
        for t_idx in range(len(discharge_row)):
            if not row_mask[t_idx]:
                continue

            lf_dt = lakeflow_datetimes[t_idx]
            if lf_dt is None:
                missing_time_counts["lakeflow"] += 1
                continue

            dval = float(discharge_row[t_idx])
            lf_date_key = lf_dt.strftime("%Y-%m-%d")

            # Match to existing SWOT pass time on the same day
            if lf_date_key in existing_times_by_date:
                matched_seconds = existing_times_by_date[lf_date_key]
                matched_dt = sos_seconds_to_datetime(matched_seconds)
            else:
                matched_seconds = float(lakeflow_times[t_idx])
                matched_dt = lf_dt

            new_records.append(DischargeRecord(
                reach_id=reach_id,
                sos_time_seconds=matched_seconds,
                sos_datetime=matched_dt,
                algorithm="lakeflow",
                variable="q_lakeflow",
                discharge_value=dval,
            ))

        if new_records:
            if reach_id in reach_data:
                reach_data[reach_id].records.extend(new_records)
                reach_data[reach_id].records.sort(key=lambda r: r.sos_time_seconds)
            else:
                new_records.sort(key=lambda r: r.sos_time_seconds)
                reach_data[reach_id] = ReachDischargeSet(reach_id=reach_id, records=new_records)


def read_sos_file(
    filepath: str,
    algorithms: list[str],
    on_reach_progress: Callable[[int], None] | None = None
) -> tuple[dict[str, ReachDischargeSet], dict[str, int]]:
    """
    Read SOS NetCDF file and return discharge data grouped by reach_id.

    Returns (reach_data dict keyed by reach_id sorted ascending, missing_time_counts per algorithm).
    """
    ds = Dataset(filepath, "r")
    try:
        reach_ids = ds["reaches"]["reach_id"][:]
        time_var = ds["reaches"]["time"]
        num_reaches = len(reach_ids)

        algo_defs = _get_algorithms(algorithms)

        # Separate lakeflow from VLen algorithms — it runs last
        vlen_algos = [a for a in algo_defs if a.name != "lakeflow"]

        # Always resolve consensus missing value — it's the fallback for metroman/hivdi
        missing_values: dict[str, float] = {}
        try:
            missing_values["consensus"] = float(ds["consensus"]["consensus_q"].missing_value)
        except (IndexError, KeyError):
            pass

        available_algos: list[AlgorithmDef] = []
        for algo in vlen_algos:
            try:
                group = ds[algo.group]
                _ = group[algo.variable]
                if algo.missing_source == "self" and algo.name not in missing_values:
                    missing_values[algo.name] = float(group[algo.variable].missing_value)
                available_algos.append(algo)
            except (IndexError, KeyError):
                logger.warning("Algorithm group '%s/%s' not found in file, skipping", algo.group, algo.variable)

        # Resolve non-self missing values
        for algo in available_algos:
            if algo.missing_source != "self" and algo.name not in missing_values:
                missing_values[algo.name] = missing_values.get(algo.missing_source, MISSING_TIME_VALUE)

        reach_data: dict[str, ReachDischargeSet] = {}
        missing_time_counts: dict[str, int] = {a.name: 0 for a in algo_defs}

        for reach_idx in range(num_reaches):
            reach_id = str(int(reach_ids[reach_idx]))
            times = np.asarray(time_var[reach_idx], dtype=np.float64)

            reach_records: list[DischargeRecord] = []

            for algo in available_algos:
                group = ds[algo.group]
                discharge_arr = np.asarray(group[algo.variable][reach_idx], dtype=np.float64)
                missing_val = missing_values.get(algo.name, missing_values.get(algo.missing_source, MISSING_TIME_VALUE))

                for t_idx in range(len(discharge_arr)):
                    dval = discharge_arr[t_idx]

                    # Skip missing discharge values
                    if dval == missing_val or np.isnan(dval):
                        continue

                    # Skip missing/invalid time
                    if t_idx >= len(times):
                        continue
                    t_val = times[t_idx]
                    if t_val == MISSING_TIME_VALUE or t_val == 0.0 or np.isnan(t_val):
                        missing_time_counts[algo.name] += 1
                        continue

                    reach_records.append(DischargeRecord(
                        reach_id=reach_id,
                        sos_time_seconds=float(t_val),
                        sos_datetime=sos_seconds_to_datetime(float(t_val)),
                        algorithm=algo.name,
                        variable=algo.variable,
                        discharge_value=float(dval),
                    ))

            if reach_records:
                reach_records.sort(key=lambda r: r.sos_time_seconds)
                reach_data[reach_id] = ReachDischargeSet(reach_id=reach_id, records=reach_records)

            if on_reach_progress:
                on_reach_progress(1)

        # Process lakeflow last so it can match to existing times
        if "lakeflow" in [a.name for a in algo_defs]:
            _read_lakeflow(ds, reach_ids, reach_data, missing_time_counts, on_reach_progress)

    finally:
        ds.close()

    # Sort by reach_id ascending (numeric sort)
    sorted_data = dict(sorted(reach_data.items(), key=lambda item: int(item[0])))
    return sorted_data, missing_time_counts
