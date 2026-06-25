"""Tests for CLI argument parsing."""
import pytest

from SOS.sos_ingest.cli import parse_args


class TestDefaultArgs:
    def test_dry_run_false_by_default(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test"])
        assert config.dry_run is False


class TestDryRunFlag:
    def test_dry_run_sets_true(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--dry-run"])
        assert config.dry_run is True


class TestAlgorithmParsing:
    def test_comma_separated_parsed(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--algorithms", "consensus,metroman"])
        assert config.algorithms == ["consensus", "metroman"]

    def test_default_is_all(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test"])
        assert config.algorithms == ["all"]


class TestRequiredSosFile:
    def test_missing_sos_file_raises(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestScanOnlyFlag:
    def test_scan_only_sets_true(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--scan-only"])
        assert config.scan_only is True


class TestYesFlag:
    def test_short_flag(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "-y"])
        assert config.yes is True

    def test_long_flag(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--yes"])
        assert config.yes is True


class TestStartReachIdArg:
    def test_parsed_into_config(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--start-reach-id", "18180900091"])
        assert config.start_reach_id == "18180900091"


class TestStopReachIdArg:
    def test_parsed_into_config(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--stop-reach-id", "18180900091"])
        assert config.stop_reach_id == "18180900091"


class TestTimeToleranceArg:
    def test_overrides_default(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--time-tolerance", "600"])
        assert config.time_tolerance_seconds == 600

    def test_default_is_3600(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test"])
        assert config.time_tolerance_seconds == 3600


class TestLimitArg:
    def test_limit_parsed(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test", "--limit", "10"])
        assert config.limit == 10

    def test_default_is_none(self):
        config = parse_args(["--sos-file", "/tmp/test.nc", "--aws-profile", "test"])
        assert config.limit is None
