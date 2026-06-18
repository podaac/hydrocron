"""CSV error log writer and summary report for SOS ingest."""
import csv
import os
from datetime import datetime, timezone

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.models import ProcessingSummary

ERROR_CSV_COLUMNS = [
    "reach_id", "sos_time", "sos_time_seconds",
    "closest_range_start_time", "time_delta_seconds", "status", "error_message", "db_table",
]


class IngestErrorLogger:
    """Writes a CSV error log for failed operations."""

    def __init__(self, output_dir: str, sos_filename: str, table_name: str = ""):
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        base = os.path.splitext(sos_filename)[0]
        self._error_path = os.path.join(output_dir, f"{base}_errors_{timestamp}.csv")
        self._summary_path = os.path.join(output_dir, f"{base}_summary_{timestamp}.txt")
        self._table_name = table_name
        self._file = open(self._error_path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=ERROR_CSV_COLUMNS)
        self._writer.writeheader()

    @property
    def error_path(self) -> str:
        """Path to the error CSV file."""
        return self._error_path

    @property
    def summary_path(self) -> str:
        """Path to the summary report file."""
        return self._summary_path

    def log(
        self,
        reach_id: str,
        sos_time: datetime | None,
        sos_time_seconds: float,
        closest_time: str | None,
        time_delta: float | None,
        status: str,
        error_message: str = "",
    ) -> None:
        """Write a single error row."""
        self._writer.writerow({
            "reach_id": reach_id,
            "sos_time": sos_time.strftime("%Y-%m-%dT%H:%M:%SZ") if sos_time else "",
            "sos_time_seconds": str(sos_time_seconds),
            "closest_range_start_time": closest_time or "",
            "time_delta_seconds": str(time_delta) if time_delta is not None else "",
            "status": status,
            "error_message": error_message,
            "db_table": self._table_name,
        })

    def flush(self) -> None:
        """Flush the CSV file to disk."""
        self._file.flush()

    def write_summary(self, summary: ProcessingSummary, config: IngestConfig | None = None) -> None:
        """Write a summary report file alongside the error CSV."""
        duration = ""
        if summary.start_time and summary.end_time:
            delta = summary.end_time - summary.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            duration = f"{minutes}m {seconds:02d}s"

        lines = [
            "SOS Discharge Ingest Summary",
            "=" * 29,
        ]
        if config:
            lines.append(f"File:           {os.path.basename(config.sos_file)}")
            lines.append(f"Table:          {config.table_name}")
            lines.append(f"Time tolerance: {config.time_tolerance_seconds}s ({config.time_tolerance_seconds // 60} min)")
        lines += [
            f"Mode:           {'DRY RUN' if summary.dry_run else 'LIVE'}",
            f"Started:        {summary.start_time.strftime('%Y-%m-%dT%H:%M:%SZ') if summary.start_time else 'N/A'}",
            f"Completed:      {summary.end_time.strftime('%Y-%m-%dT%H:%M:%SZ') if summary.end_time else 'N/A'}",
            f"Duration:       {duration}",
            "",
            f"Total reaches in SOS file: {summary.total_reaches:,}",
            f"Reaches processed: {summary.reaches_processed:,}",
            f"Reaches skipped: {summary.reaches_skipped:,}",
            f"Reaches not in DB: {summary.no_rows:,}",
            "",
            f"Total time steps attempted: {summary.total_time_steps:,}",
            f"  Matched:                        {summary.matched:,}",
            f"  Updated:                        {summary.updated:,}",
            f"  No time match (outside tolerance): {summary.no_match:,}",
            f"  Ambiguous match:                {summary.ambiguous_match:,}",
            f"  Skipped (unchanged):            {summary.skipped_unchanged:,}",
            f"  Write errors:                   {summary.write_errors:,}",
            "",
            f"Last reach ID processed: {summary.last_reach_id or 'N/A'}",
            f"To resume: --start-reach-id {summary.last_reach_id}" if summary.last_reach_id else "",
        ]

        with open(self._summary_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    def close(self) -> None:
        """Flush and close the CSV file."""
        self._file.flush()
        self._file.close()
