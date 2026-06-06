"""Tests for CLI argument parsing."""
import pytest

from SOS.sos_ingest.cli import parse_args


class TestDefaultArgs:
    def test_dry_run_false_by_default(self):
        config = parse_args(["--sos-file", "/tmp/test.nc"])
        assert config.dry_run is False


class TestDryRunFlag:
    def test_dry_run_sets_true(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--dry-run"])
        assert config.dry_run is True


class TestAlgorithmParsing:
    def test_comma_separated_parsed(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--algorithms", "consensus,metroman"])
        assert config.algorithms == ["consensus", "metroman"]

    def test_default_is_all(self):
        config = parse_args(["--sos-file", "/tmp/test.nc"])
        assert config.algorithms == ["all"]


class TestRequiredSosFile:
    def test_missing_sos_file_raises(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestScanOnlyFlag:
    def test_scan_only_sets_true(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--scan-only"])
        assert config.scan_only is True


class TestYesFlag:
    def test_short_flag(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "-y"])
        assert config.yes is True

    def test_long_flag(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--yes"])
        assert config.yes is True


class TestStartReachIdArg:
    def test_parsed_into_config(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--start-reach-id", "18180900091"])
        assert config.start_reach_id == "18180900091"


class TestStopReachIdArg:
    def test_parsed_into_config(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--stop-reach-id", "18180900091"])
        assert config.stop_reach_id == "18180900091"


class TestTimeToleranceArg:
    def test_overrides_default(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--time-tolerance", "600"])
        assert config.time_tolerance_seconds == 600

    def test_default_is_900(self):
        config = parse_args(["--sos-file", "/tmp/test.nc"])
        assert config.time_tolerance_seconds == 900
