"""Tests for Rich UI components."""
import io
from datetime import datetime, timezone
from unittest.mock import patch

from rich.console import Console

from SOS.sos_ingest.config import IngestConfig
from SOS.sos_ingest.models import ProcessingSummary, ReachDischargeSet, DischargeRecord
from SOS.sos_ingest.ui import IngestUI


def _make_config(**kwargs) -> IngestConfig:
    defaults = {"sos_file": "/tmp/test.nc", "aws_profile": None, "dry_run": True}
    defaults.update(kwargs)
    return IngestConfig(**defaults)


def _make_reach_data() -> dict[str, ReachDischargeSet]:
    dt = datetime(2023, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
    records = [DischargeRecord("10000000021", 748617713.0, dt, "consensus", "consensus_q", 28.95)]
    return {"10000000021": ReachDischargeSet("10000000021", records)}


def _make_summary(**kwargs) -> ProcessingSummary:
    defaults = {
        "total_reaches": 100,
        "reaches_processed": 80,
        "reaches_skipped": 20,
        "total_time_steps": 500,
        "matched": 400,
        "updated": 375,
        "no_match": 50,
        "no_rows": 20,
        "ambiguous_match": 2,
        "skipped_unchanged": 25,
        "write_errors": 3,
        "dry_run": False,
        "last_reach_id": "18180900091",
        "start_time": datetime(2026, 5, 6, 10, 0, 0, tzinfo=timezone.utc),
        "end_time": datetime(2026, 5, 6, 10, 15, 0, tzinfo=timezone.utc),
    }
    defaults.update(kwargs)
    return ProcessingSummary(**defaults)


class TestPreflightSummaryShowsCounts:
    def test_panel_displays_reach_and_timestep_counts(self):
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        ui = IngestUI(console=console)
        config = _make_config(yes=True)
        reach_data = _make_reach_data()

        ui.show_preflight_summary(config, reach_data, reaches_to_process=1, timesteps_to_process=1)

        text = output.getvalue()
        assert "1" in text  # reaches to process
        assert "Pre-flight Summary" in text


class TestPreflightPromptYesReturnsTrue:
    def test_y_input_returns_true(self):
        console = Console(file=io.StringIO(), force_terminal=True, width=120)
        ui = IngestUI(console=console)
        config = _make_config()
        reach_data = _make_reach_data()

        with patch.object(console, "input", return_value="y"):
            result = ui.show_preflight_summary(config, reach_data, 1, 1)
        assert result is True


class TestPreflightPromptNoReturnsFalse:
    def test_n_input_returns_false(self):
        console = Console(file=io.StringIO(), force_terminal=True, width=120)
        ui = IngestUI(console=console)
        config = _make_config()
        reach_data = _make_reach_data()

        with patch.object(console, "input", return_value="n"):
            result = ui.show_preflight_summary(config, reach_data, 1, 1)
        assert result is False


class TestYesFlagSkipsPrompt:
    def test_no_prompt_shown_returns_true(self):
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        ui = IngestUI(console=console)
        config = _make_config(yes=True)
        reach_data = _make_reach_data()

        result = ui.show_preflight_summary(config, reach_data, 1, 1)
        assert result is True
        assert "proceeding automatically" in output.getvalue()


class TestCompletionSummaryShowsLastReachId:
    def test_last_reach_id_in_panel(self):
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        ui = IngestUI(console=console)
        summary = _make_summary()

        ui.show_completion_summary(summary, "/tmp/errors.csv", "/tmp/summary.txt")

        text = output.getvalue()
        assert "18180900091" in text
        assert "--start-reach-id" in text


class TestCompletionSummaryPartialRun:
    def test_partial_stats_displayed(self):
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        ui = IngestUI(console=console)
        summary = _make_summary(
            reaches_processed=30,
            total_time_steps=200,
            matched=150,
            last_reach_id="18180900041",
        )

        ui.show_completion_summary(summary, "/tmp/errors.csv", "/tmp/summary.txt")

        text = output.getvalue()
        assert "30" in text
        assert "18180900041" in text
