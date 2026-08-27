"""CLI entry point for SOS discharge ingest."""
import argparse
import logging

from SOS.sos_ingest.config import IngestConfig


def parse_args(argv: list[str] | None = None) -> IngestConfig:
    """Parse CLI arguments and return an IngestConfig."""
    parser = argparse.ArgumentParser(
        prog="sos_ingest",
        description="Ingest SWOT SOS discharge results into Hydrocron DynamoDB reach table.",
    )
    parser.add_argument("--sos-file", required=True, help="Path to SOS NetCDF results file")
    parser.add_argument("--table-name", default="hydrocron-swot-reach-table", help="DynamoDB table name")
    parser.add_argument("--dry-run", action="store_true", help="Preview mode, no DB writes")
    parser.add_argument("--start-reach-id", default=None, help="Reach ID to resume from")
    parser.add_argument("--stop-reach-id", default=None, help="Reach ID to stop after (inclusive)")
    parser.add_argument("--limit", type=int, default=None, help="Max number of reaches to process")
    parser.add_argument("--time-tolerance", type=int, default=3600, help="Max seconds for time matching (default: 3600)")
    parser.add_argument("--output-dir", default="./output", help="Directory for error log and summary")
    parser.add_argument("--algorithms", default="all", help="Comma-separated algorithms or 'all'")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    parser.add_argument("--aws-profile", required=True, help="AWS profile name (from ~/.aws/credentials)")
    parser.add_argument("--scan-only", action="store_true", help="Post-ingest verification mode (read-only)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args(argv)

    algorithms = [a.strip() for a in args.algorithms.split(",")]

    return IngestConfig(
        sos_file=args.sos_file,
        table_name=args.table_name,
        dry_run=args.dry_run,
        start_reach_id=args.start_reach_id,
        stop_reach_id=args.stop_reach_id,
        limit=args.limit,
        time_tolerance_seconds=args.time_tolerance,
        output_dir=args.output_dir,
        algorithms=algorithms,
        log_level=args.log_level,
        scan_only=args.scan_only,
        yes=args.yes,
        aws_profile=args.aws_profile,
    )


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    config = parse_args(argv)
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO))

    if config.scan_only:
        try:
            from SOS.sos_ingest.scanner import scan  # noqa: E501
        except ImportError as e:
            raise SystemExit(
                "ERROR: Optional SOS ingest dependencies are not installed. "
                "Install with `poetry install --with sos` (or add rich/netCDF4 to your environment)."
            ) from e
        scan(config)
    else:
        try:
            from SOS.sos_ingest.processor import run  # noqa: E501
        except ImportError as e:
            raise SystemExit(
                "ERROR: Optional SOS ingest dependencies are not installed. "
                "Install with `poetry install --with sos` (or add rich/netCDF4 to your environment)."
            ) from e
        run(config)


if __name__ == "__main__":
    main()
