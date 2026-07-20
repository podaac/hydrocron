"""Shared helpers for processor and scanner."""
from datetime import datetime, timezone


def parse_db_times(rows: list[dict]) -> list[tuple[str, datetime]]:
    """Parse range_start_time strings from DB rows into sorted (str, datetime) pairs."""
    parsed = []
    for row in rows:
        rst = row.get("range_start_time", "")
        if not rst:
            continue
        try:
            dt = datetime.strptime(rst, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            parsed.append((rst, dt))
        except ValueError:
            continue
    parsed.sort(key=lambda x: x[1])
    return parsed


def find_db_row(rows: list[dict], range_start_time: str) -> dict | None:
    """Find the DB row matching a specific range_start_time."""
    for row in rows:
        if row.get("range_start_time") == range_start_time:
            return row
    return None
