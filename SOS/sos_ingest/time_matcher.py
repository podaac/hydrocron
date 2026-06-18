"""Time matching logic — finds closest DB range_start_time for an SOS timestamp."""
from bisect import bisect_left
from datetime import datetime


def find_closest_time(
    sos_datetime: datetime,
    db_times: list[tuple[str, datetime]],
    tolerance_seconds: int
) -> tuple[str | None, float | None, str]:
    """
    Find the DB range_start_time closest to sos_datetime within tolerance.

    Parameters
    ----------
    sos_datetime : datetime
        The SOS timestamp to match.
    db_times : list of (range_start_time_str, parsed_datetime)
        Sorted ascending by datetime.
    tolerance_seconds : int
        Maximum allowed delta in seconds.

    Returns
    -------
    tuple of (matched_range_start_time, delta_seconds, status)
        status is "matched", "no_match", or "ambiguous_match".
        On "no_match", delta_seconds is the closest distance found (or None if db_times is empty).
    """
    if not db_times:
        return None, None, "no_match"

    datetimes = [dt for _, dt in db_times]
    pos = bisect_left(datetimes, sos_datetime)

    candidates: list[tuple[str, float]] = []

    if pos > 0:
        key_left, dt_left = db_times[pos - 1]
        delta_left = abs((sos_datetime - dt_left).total_seconds())
        candidates.append((key_left, delta_left))

    if pos < len(db_times):
        key_right, dt_right = db_times[pos]
        delta_right = abs((sos_datetime - dt_right).total_seconds())
        candidates.append((key_right, delta_right))

    if not candidates:
        return None, None, "no_match"

    best = min(candidates, key=lambda c: c[1])

    if best[1] > tolerance_seconds:
        return None, best[1], "no_match"

    if len(candidates) == 2 and candidates[0][1] == candidates[1][1]:
        return None, candidates[0][1], "ambiguous_match"

    return best[0], best[1], "matched"
