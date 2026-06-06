"""Data models for SOS ingest."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AlgorithmDef:
    """Configuration for one SOS discharge algorithm."""

    name: str
    group: str
    variable: str
    missing_source: str
    column_name: str


@dataclass
class DischargeRecord:
    """A single discharge value from the SOS file."""

    reach_id: str
    sos_time_seconds: float
    sos_datetime: datetime
    algorithm: str
    variable: str
    discharge_value: float


@dataclass
class ReachDischargeSet:
    """All discharge records for a single reach_id, across algorithms."""

    reach_id: str
    records: list[DischargeRecord] = field(default_factory=list)


@dataclass
class ProcessingSummary:
    """Final summary statistics."""

    total_reaches: int
    reaches_processed: int
    reaches_skipped: int
    total_time_steps: int
    matched: int
    updated: int
    no_match: int
    no_rows: int
    ambiguous_match: int
    skipped_unchanged: int
    write_errors: int
    dry_run: bool
    last_reach_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass
class ScanSummary:
    """Summary of post-ingest verification."""

    total_reaches: int
    total_time_steps: int
    ok: int
    no_rows: int
    no_time_match: int
    missing_column: int
    value_mismatch: int
    source_mismatch: int
