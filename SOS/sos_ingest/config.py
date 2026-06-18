"""Runtime configuration for SOS ingest."""
from dataclasses import dataclass, field


@dataclass
class IngestConfig:
    """All runtime configuration, created from CLI args."""

    sos_file: str
    aws_profile: str | None = None
    table_name: str = "hydrocron-swot-reach-table"
    dry_run: bool = False
    start_reach_id: str | None = None
    stop_reach_id: str | None = None
    limit: int | None = None
    time_tolerance_seconds: int = 900
    output_dir: str = "./output"
    algorithms: list[str] = field(default_factory=lambda: ["all"])
    log_level: str = "INFO"
    scan_only: bool = False
    yes: bool = False
