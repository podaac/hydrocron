"""Rich console UI for SOS ingest — progress bars, panels, confirmation prompt."""
import os
from collections import defaultdict

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
from rich.table import Table
from rich.text import Text

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.models import ProcessingSummary, ReachDischargeSet, ScanSummary


class _StatusProgress(Progress):
    """Progress bar that renders a status line below the bar, left-aligned."""

    def get_renderable(self):
        table = self.make_tasks_table(self.tasks)
        status = ""
        if self.tasks:
            status = self.tasks[0].fields.get("status", "")
        if status:
            return Group(table, Text(status))
        return table


class IngestUI:
    """Rich-based CLI interface for operator feedback."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def create_reading_progress(self, total_reaches: int) -> Progress:
        """Returns a Rich Progress instance for the file-reading phase."""
        progress = Progress(
            TextColumn("[bold blue]Reading SOS file"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("reaches"),
            TimeElapsedColumn(),
            console=self.console,
        )
        progress.add_task("reading", total=total_reaches)
        return progress

    def show_preflight_summary(
        self,
        config: IngestConfig,
        reach_data: dict[str, ReachDischargeSet],
        reaches_to_process: int,
        timesteps_to_process: int,
        missing_time_counts: dict[str, int] | None = None,
    ) -> bool:
        """Display pre-ingest summary and prompt for confirmation. Returns True to proceed."""
        mode = "[bold red]DRY RUN[/]" if config.dry_run else "[bold green]LIVE[/]"
        algos = ", ".join(config.algorithms)
        if missing_time_counts is None:
            missing_time_counts = {}

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("File:", os.path.basename(config.sos_file))
        table.add_row("Table:", config.table_name)
        table.add_row("Mode:", mode)
        table.add_row("Time tolerance:", f"{config.time_tolerance_seconds}s ({config.time_tolerance_seconds // 60} min)")
        table.add_row("Algorithms:", algos)
        table.add_row("", "")
        table.add_row("Reaches found:", f"{len(reach_data):,}")
        if config.start_reach_id:
            table.add_row("Start reach ID:", f"{config.start_reach_id} (resume)")
        if config.stop_reach_id:
            table.add_row("Stop reach ID:", f"{config.stop_reach_id}")
        table.add_row("Reaches to process:", f"{reaches_to_process:,}")
        table.add_row("Time steps to process:", f"~{timesteps_to_process:,}")

        # Per-algorithm breakdown
        algo_stats: dict[str, dict] = defaultdict(lambda: {"reaches": 0, "values": 0})
        for rds in reach_data.values():
            seen_algos: set[str] = set()
            for rec in rds.records:
                algo_stats[rec.algorithm]["values"] += 1
                if rec.algorithm not in seen_algos:
                    algo_stats[rec.algorithm]["reaches"] += 1
                    seen_algos.add(rec.algorithm)
        if algo_stats:
            table.add_row("", "")
            table.add_row("Per-algorithm breakdown:", "")
            for algo_name in sorted(algo_stats.keys()):
                stats = algo_stats[algo_name]
                invalid = missing_time_counts.get(algo_name, 0)
                parts = f"{stats['reaches']:,} reaches, {stats['values']:,} values"
                if invalid > 0:
                    parts += f", {invalid:,} invalid times"
                table.add_row(f"  {algo_name}:", parts)

        self.console.print(Panel(table, title="SOS Ingest — Pre-flight Summary", border_style="blue"))

        if config.yes:
            self.console.print("[dim]--yes flag set, proceeding automatically[/]")
            return True

        response = self.console.input("\nProceed with ingest? [y/N]: ").strip().lower()
        return response == "y"

    def create_progress_bar(self, total_timesteps: int) -> Progress:
        """Returns a configured Rich Progress instance for the update loop."""
        progress = _StatusProgress(
            TextColumn("[bold green]Updating DynamoDB"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("time steps"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        progress.add_task("updating", total=total_timesteps, status="")
        return progress

    def show_completion_summary(self, summary: ProcessingSummary, error_log_path: str, summary_path: str) -> None:
        """Display the final results panel."""
        duration = ""
        if summary.start_time and summary.end_time:
            delta = summary.end_time - summary.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            duration = f"{minutes}m {seconds:02d}s"

        total = summary.total_time_steps or 1

        def pct(n: int) -> str:
            return f"{n / total * 100:.1f}%"

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Duration:", duration)
        table.add_row("Reaches:", f"{summary.reaches_processed:,} processed, {summary.reaches_skipped:,} skipped")
        table.add_row("Reaches not in DB:", f"{summary.no_rows:,}")
        table.add_row("", "")
        table.add_row("Time steps:", f"{summary.total_time_steps:,} attempted")
        table.add_row("  ✓ Matched:", f"{summary.matched:,} ({pct(summary.matched)})")
        table.add_row("  ✓ Updated:", f"{summary.updated:,} ({pct(summary.updated)})")
        table.add_row("  ✗ No time match:", f"{summary.no_match:,} ({pct(summary.no_match)})")
        table.add_row("  ✗ Ambiguous match:", f"{summary.ambiguous_match:,} ({pct(summary.ambiguous_match)})")
        table.add_row("  ○ Skipped (unchanged):", f"{summary.skipped_unchanged:,} ({pct(summary.skipped_unchanged)})")
        table.add_row("  ✗ Write errors:", f"{summary.write_errors:,} ({pct(summary.write_errors)})")
        table.add_row("", "")
        table.add_row("Last reach ID:", summary.last_reach_id or "N/A")
        if summary.last_reach_id:
            table.add_row("Resume cmd:", f"--start-reach-id {summary.last_reach_id}")
        table.add_row("", "")
        table.add_row("Error log:", error_log_path)
        table.add_row("Summary:", summary_path)

        title = "SOS Ingest — Complete" if not summary.dry_run else "SOS Ingest — Complete (DRY RUN)"
        self.console.print(Panel(table, title=title, border_style="green"))

    def create_scan_progress(self, total_steps: int) -> Progress:
        """Returns a Rich Progress instance for the scan phase."""
        progress = Progress(
            TextColumn("[bold green]Scanning"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("time steps"),
            TimeElapsedColumn(),
            console=self.console,
        )
        progress.add_task("scanning", total=total_steps)
        return progress

    def show_scan_results(self, summary: ScanSummary, config: IngestConfig, scan_path: str, discrepancies: list[dict]) -> None:
        """Display the scan results panel and sample discrepancy table."""
        total = summary.total_time_steps or 1

        def pct(n: int) -> str:
            return f"{n / total * 100:.1f}%"

        result_table = Table(show_header=False, box=None, padding=(0, 2))
        result_table.add_column(style="bold")
        result_table.add_column()
        result_table.add_row("File:", os.path.basename(config.sos_file))
        result_table.add_row("Table:", config.table_name)
        result_table.add_row("Time tolerance:", f"{config.time_tolerance_seconds}s ({config.time_tolerance_seconds // 60} min)")
        result_table.add_row("", "")
        result_table.add_row("Total reaches scanned:", f"{summary.total_reaches:,}")
        result_table.add_row("Reaches not in DB:", f"{summary.no_rows:,}")
        result_table.add_row("", "")
        result_table.add_row("Total time steps:", f"{summary.total_time_steps:,}")
        result_table.add_row("  ✓ OK:", f"{summary.ok:,} ({pct(summary.ok)})")
        result_table.add_row("  ✗ No time match:", f"{summary.no_time_match:,} ({pct(summary.no_time_match)})")
        result_table.add_row("  ✗ Missing column:", f"{summary.missing_column:,} ({pct(summary.missing_column)})")
        result_table.add_row("  ✗ Value mismatch:", f"{summary.value_mismatch:,} ({pct(summary.value_mismatch)})")
        result_table.add_row("", "")
        result_table.add_row("Scan report:", scan_path)

        self.console.print(Panel(result_table, title="SOS Ingest — Scan Results", border_style="blue"))

        if discrepancies:
            sample_table = Table(title=f"Sample discrepancies (first {min(10, len(discrepancies))})")
            sample_table.add_column("reach_id")
            sample_table.add_column("sos_time")
            sample_table.add_column("column")
            sample_table.add_column("status")
            sample_table.add_column("expected")
            sample_table.add_column("actual")
            for d in discrepancies[:10]:
                sample_table.add_row(
                    d["reach_id"], d["sos_time"], d["column"],
                    d["status"], d["expected_value"][:20], d["actual_value"][:20],
                )
            self.console.print(sample_table)
