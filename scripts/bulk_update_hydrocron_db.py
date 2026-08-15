"""Bulk-set fixed string values on every row of one Hydrocron DynamoDB table.

Rows that already contain all requested values are skipped. Use --dry-run first,
then run another dry-run after a live update to verify that no mismatches remain.
"""
import argparse
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer


CHECKPOINT_PAGES_DEFAULT = 300
PROGRESS_PAGES_DEFAULT = 10
WORKERS_DEFAULT = 16
WORKERS_MAX = 64


def positive_int(value):
    """Parse a strictly positive integer for argparse."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def worker_count(value):
    """Parse a safe worker count for argparse."""
    parsed = positive_int(value)
    if parsed > WORKERS_MAX:
        raise argparse.ArgumentTypeError(f"must not exceed {WORKERS_MAX}")
    return parsed


def parse_updates(pairs):
    """Parse unique column=value pairs into an insertion-ordered dictionary."""
    updates = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"'{pair}' is not a column=value pair")
        column, value = pair.split("=", 1)
        column, value = column.strip(), value.strip()
        if not column or not value:
            raise ValueError(f"'{pair}' has an empty column or value")
        if column in updates:
            raise ValueError(f"column '{column}' was provided more than once")
        updates[column] = value
    return updates


def parse_start_key(raw):
    """Parse a JSON object supplied to --start-key."""
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--start-key is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("--start-key must be a JSON object")
    return value


def get_key_columns(key_schema):
    """Return partition key, optional sort key, and ordered key-column list."""
    by_type = {entry["KeyType"]: entry["AttributeName"] for entry in key_schema}
    if "HASH" not in by_type:
        raise ValueError("table key schema has no HASH key")
    partition_key = by_type["HASH"]
    sort_key = by_type.get("RANGE")
    return partition_key, sort_key, [partition_key] + ([sort_key] if sort_key else [])


def validate_inputs(updates, start_key, key_columns, attribute_definitions):
    """Validate targets and an optional resume key against the table schema."""
    key_targets = set(updates).intersection(key_columns)
    if key_targets:
        names = ", ".join(sorted(key_targets))
        raise ValueError(f"primary-key columns cannot be updated: {names}")

    if start_key is None:
        return
    expected = set(key_columns)
    actual = set(start_key)
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        details = []
        if missing:
            details.append(f"missing: {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected: {', '.join(sorted(extra))}")
        raise ValueError(f"--start-key fields do not match the table key ({'; '.join(details)})")

    attribute_types = {item["AttributeName"]: item["AttributeType"] for item in attribute_definitions}
    for column in key_columns:
        if attribute_types.get(column) == "S" and not isinstance(start_key[column], str):
            raise ValueError(f"--start-key field '{column}' must be a JSON string")


def build_update_args(table_name, key, updates, key_columns):
    """Build a low-level client request that cannot recreate a deleted item."""
    serializer = TypeSerializer()
    set_parts = [f"#c{i} = :v{i}" for i in range(len(updates))]
    names = {f"#c{i}": column for i, column in enumerate(updates)}
    names.update({f"#k{i}": column for i, column in enumerate(key_columns)})
    return {
        "TableName": table_name,
        "Key": {column: serializer.serialize(value) for column, value in key.items()},
        "UpdateExpression": "SET " + ", ".join(set_parts),
        "ExpressionAttributeNames": names,
        "ExpressionAttributeValues": {
            f":v{i}": serializer.serialize(value)
            for i, value in enumerate(updates.values())
        },
        "ConditionExpression": " AND ".join(f"attribute_exists(#k{i})" for i in range(len(key_columns))),
        "ReturnConsumedCapacity": "INDEXES",
        "ReturnValues": "UPDATED_OLD",
    }


def _run_update(client, request):
    """Issue one low-level update_item call in a worker thread."""
    return client.update_item(**request)


def write_summary(path, details):
    """Write the final status and counters for a run."""
    with open(path, "w", encoding="utf-8") as log:
        log.write("Hydrocron Bulk Field Update\n===========================\n")
        for label, value in details.items():
            log.write(f"{label}: {value}\n")


def _resume_text(resume_key):
    if resume_key is None:
        return "omit --start-key (restart from the beginning)"
    return f"--start-key '{json.dumps(resume_key, separators=(',', ':'))}'"


def _capacity_breakdown(response):
    """Return reported total, base-table, and GSI capacity units."""
    if not response or "ConsumedCapacity" not in response:
        return 0.0, 0.0, 0.0
    consumed = response["ConsumedCapacity"]
    total = float(consumed.get("CapacityUnits", 0))
    table = float(consumed.get("Table", {}).get("CapacityUnits", 0))
    indexes = sum(
        float(details.get("CapacityUnits", 0))
        for details in consumed.get("GlobalSecondaryIndexes", {}).values()
    )
    return total, table, indexes


def main(argv=None):
    """Scan a table and set fixed field values on rows that differ."""
    parser = argparse.ArgumentParser(prog="bulk_update_hydrocron_db")
    parser.add_argument("table_name", help="DynamoDB table to update (one per run)")
    parser.add_argument("updates", nargs="+", help="unique column=value pairs")
    parser.add_argument("--aws-profile", default=None, help="AWS profile name")
    parser.add_argument("--output-dir", default="bulk_output", help="directory for timestamped output files")
    parser.add_argument("--start-key", default=None, help="JSON LastEvaluatedKey to resume from")
    parser.add_argument("--limit", type=positive_int, default=None, help="stop after this many updates")
    parser.add_argument(
        "--max-rows-read", type=positive_int, default=None,
        help="stop after scanning at most this many rows (for cost-bounded testing)",
    )
    parser.add_argument(
        "--checkpoint-pages", type=positive_int, default=CHECKPOINT_PAGES_DEFAULT,
        help=f"print a resume checkpoint every N pages (default: {CHECKPOINT_PAGES_DEFAULT})",
    )
    parser.add_argument(
        "--progress-pages", type=positive_int, default=PROGRESS_PAGES_DEFAULT,
        help=f"print the progress counters every N pages (default: {PROGRESS_PAGES_DEFAULT})",
    )
    parser.add_argument(
        "--workers", type=worker_count, default=WORKERS_DEFAULT,
        help=f"concurrent update requests; 1 disables concurrency (default: {WORKERS_DEFAULT})",
    )
    parser.add_argument("--dry-run", action="store_true", help="preview only; make no DynamoDB writes")
    parser.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompt")
    args = parser.parse_args(argv)

    # Flush each line as it is printed so progress is visible in real time even when
    # stdout is redirected or run over SSM/screen (Python block-buffers a non-TTY otherwise).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    try:
        updates = parse_updates(args.updates)
        initial_start_key = parse_start_key(args.start_key)
    except ValueError as exc:
        parser.error(str(exc))

    start_time = datetime.now(timezone.utc)
    timestamp = start_time.strftime("%Y%m%dT%H%M%S%fZ")
    os.makedirs(args.output_dir, exist_ok=True)
    base = os.path.join(args.output_dir, f"{args.table_name}_{timestamp}")
    log_path = f"{base}_log.txt"
    dry_path = f"{base}_dry_run.csv"
    error_path = f"{base}_errors.csv"

    rows_read = rows_examined = rows_updated = rows_skipped = errors = pages = 0
    rows_changed = redundant_writes = 0
    read_capacity_units = write_capacity_units = 0.0
    table_write_capacity_units = gsi_write_capacity_units = 0.0
    status = "FAILED"
    failure_message = ""
    resume_key = initial_start_key
    page_start_key = initial_start_key
    partition_key = sort_key = None
    key_columns = []
    dry_file = error_file = None
    dry_writer = error_writer = None

    updates_display = ", ".join(f"{key}={value}" for key, value in updates.items())
    mode = "DRY RUN" if args.dry_run else "LIVE"
    start_key_display = json.dumps(initial_start_key, separators=(",", ":")) if initial_start_key else "beginning"
    approx_rows_display = "unknown"

    try:
        config = Config(
            retries={"max_attempts": 5, "mode": "adaptive"},
            max_pool_connections=args.workers,
        )
        session = boto3.Session(profile_name=args.aws_profile) if args.aws_profile else boto3.Session()
        table = session.resource("dynamodb", config=config).Table(args.table_name)
        update_client = session.client("dynamodb", config=config)
        partition_key, sort_key, key_columns = get_key_columns(table.key_schema)
        validate_inputs(updates, initial_start_key, key_columns, table.attribute_definitions)
        deserializer = TypeDeserializer()

        approx_rows = getattr(table, "item_count", None)
        if approx_rows is not None:
            approx_rows_display = f"~{approx_rows:,}"

        limit_display = args.limit if args.limit is not None else "none"
        read_limit_display = args.max_rows_read if args.max_rows_read is not None else "none"
        print(
            f"Table:      {args.table_name}\nUpdates:    {updates_display}\nMode:       {mode}\n"
            f"Approx rows: {approx_rows_display}\n"
            f"Update cap: {limit_display}\nRead cap:   {read_limit_display}\n"
            f"Workers:    {args.workers}\nStart key:  {start_key_display}"
        )
        print("Note: confirmation occurs before scanning; run --dry-run to obtain the mismatch count.")
        if not args.yes and input("Proceed? [y/N]: ").strip().lower() != "y":
            status = "ABORTED"
        else:
            if args.dry_run:
                dry_file = open(dry_path, "w", newline="", encoding="utf-8")
                dry_writer = csv.writer(dry_file)
                dry_writer.writerow([partition_key, sort_key or "", "columns"])

            all_columns = key_columns + list(updates)
            projection = ", ".join(f"#p{i}" for i in range(len(all_columns)))
            projection_names = {f"#p{i}": column for i, column in enumerate(all_columns)}
            status = "RUNNING"

            def record_completed_future(future, item, row_updates):
                """Aggregate one completed worker result on the main thread."""
                nonlocal rows_updated, rows_changed, redundant_writes, errors
                nonlocal write_capacity_units, table_write_capacity_units, gsi_write_capacity_units
                nonlocal error_file, error_writer

                try:
                    update_response = future.result()
                    total_units, table_units, index_units = _capacity_breakdown(update_response)
                    write_capacity_units += total_units
                    table_write_capacity_units += table_units
                    gsi_write_capacity_units += index_units

                    old_values = {
                        column: deserializer.deserialize(value)
                        for column, value in update_response.get("Attributes", {}).items()
                    }
                    actually_changed = any(
                        old_values.get(column) != value
                        for column, value in row_updates.items()
                    )
                    if actually_changed:
                        rows_changed += 1
                    else:
                        redundant_writes += 1
                    rows_updated += 1
                except Exception as exc:
                    errors += 1
                    if error_file is None:
                        error_file = open(error_path, "w", newline="", encoding="utf-8")
                        error_writer = csv.writer(error_file)
                        error_writer.writerow([partition_key, sort_key or "", "error_message"])
                    if isinstance(exc, ClientError):
                        message = exc.response.get("Error", {}).get("Message", str(exc))
                    else:
                        message = f"{type(exc).__name__}: {exc}"
                    error_writer.writerow(
                        [item[partition_key], item.get(sort_key, "") if sort_key else "", message]
                    )

            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                while status == "RUNNING":
                    scan_args = {
                        "ProjectionExpression": projection,
                        "ExpressionAttributeNames": projection_names,
                        "ReturnConsumedCapacity": "INDEXES",
                    }
                    if page_start_key is not None:
                        scan_args["ExclusiveStartKey"] = page_start_key
                    if args.max_rows_read is not None:
                        scan_args["Limit"] = args.max_rows_read - rows_read
                    page = table.scan(**scan_args)
                    pages += 1
                    rows_read += page.get("ScannedCount", len(page.get("Items", [])))
                    scan_units, _, _ = _capacity_breakdown(page)
                    read_capacity_units += scan_units

                    # Collect rows needing an update (main thread; cheap in-memory diff).
                    page_tasks = []
                    for item in page.get("Items", []):
                        if args.limit is not None and (rows_updated + len(page_tasks)) >= args.limit:
                            status = "LIMITED"
                            resume_key = page_start_key
                            break

                        rows_examined += 1
                        row_updates = {
                            column: value
                            for column, value in updates.items()
                            if item.get(column) != value
                        }
                        if not row_updates:
                            rows_skipped += 1
                            continue

                        key = {column: item[column] for column in key_columns}
                        if args.dry_run:
                            row_updates_csv = "; ".join(
                                f"{column}={value}" for column, value in row_updates.items()
                            )
                            dry_writer.writerow(
                                [item[partition_key], item.get(sort_key, "") if sort_key else "", row_updates_csv]
                            )
                            rows_updated += 1
                            continue

                        request = build_update_args(args.table_name, key, row_updates, key_columns)
                        page_tasks.append((item, row_updates, request))

                    # Submit bounded waves so a systematic failure can stop the run without
                    # first submitting an entire scan page.
                    task_index = 0
                    while task_index < len(page_tasks):
                        batch = page_tasks[task_index:task_index + args.workers]
                        futures = {
                            executor.submit(_run_update, update_client, request): (item, row_updates)
                            for item, row_updates, request in batch
                        }
                        processed = set()
                        interrupted = False
                        try:
                            for future in as_completed(futures):
                                processed.add(future)
                                item, row_updates = futures[future]
                                record_completed_future(future, item, row_updates)
                        except KeyboardInterrupt:
                            interrupted = True
                            for future in futures:
                                if not future.done():
                                    future.cancel()
                            # Account for every request that was already running. Cancelled queued
                            # requests are intentionally left for the page-level resume.
                            for future in as_completed(futures):
                                if future in processed or future.cancelled():
                                    continue
                                processed.add(future)
                                item, row_updates = futures[future]
                                record_completed_future(future, item, row_updates)

                        if interrupted:
                            raise KeyboardInterrupt
                        task_index += len(batch)
                        if errors:
                            raise RuntimeError(
                                f"aborted after {errors} row update error(s) in the current worker wave"
                            )

                    if dry_file:
                        dry_file.flush()
                    if error_file:
                        error_file.flush()

                    next_key = page.get("LastEvaluatedKey")
                    if status == "RUNNING" and next_key:
                        if args.limit is not None and rows_updated >= args.limit:
                            status = "LIMITED"
                            resume_key = next_key
                        elif args.max_rows_read is not None and rows_read >= args.max_rows_read:
                            status = "READ_LIMITED"
                            resume_key = next_key

                    is_last_page = status != "RUNNING" or not next_key
                    if is_last_page or pages % args.progress_pages == 0:
                        pct = f"{min(100.0, rows_read / approx_rows * 100):.1f}%" if approx_rows else "?%"
                        print(
                            f"  {pct} read={rows_read:,} examined={rows_examined:,} updated={rows_updated:,} "
                            f"changed={rows_changed:,} redundant={redundant_writes:,} "
                            f"skipped={rows_skipped:,} errors={errors} "
                            f"read_units={read_capacity_units:,.3f} write_units={write_capacity_units:,.3f}"
                        )

                    if status != "RUNNING":
                        break

                    if next_key and pages % args.checkpoint_pages == 0:
                        print(f"Checkpoint: {_resume_text(next_key)}")
                    if not next_key:
                        status = "COMPLETED"
                        resume_key = None
                        break
                    page_start_key = next_key
                    resume_key = next_key

    except KeyboardInterrupt:
        status = "INTERRUPTED"
        resume_key = initial_start_key if errors else page_start_key
        failure_message = "interrupted by user"
    except Exception as exc:  # Ensure every operational failure is summarized and exits nonzero.
        status = "FAILED"
        resume_key = initial_start_key if errors else page_start_key
        failure_message = str(exc)
    finally:
        if dry_file:
            dry_file.close()
        if error_file:
            error_file.close()
        end_time = datetime.now(timezone.utc)
        details = {
            "Status": status,
            "Table": args.table_name,
            "Updates": updates_display,
            "Mode": mode,
            "Workers": args.workers,
            "Update limit": args.limit if args.limit is not None else "none",
            "Maximum rows read": args.max_rows_read if args.max_rows_read is not None else "none",
            "Start key": start_key_display,
            "Approximate table rows": approx_rows_display,
            "Started": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Finished": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Duration": end_time - start_time,
            "Pages read": pages,
            "Rows read": rows_read,
            "Rows examined": rows_examined,
            "Rows updated": rows_updated,
            "Rows actually changed": rows_changed,
            "Redundant successful writes": redundant_writes,
            "Rows skipped": rows_skipped,
            "Errors": errors,
            "Reported read capacity units": f"{read_capacity_units:.3f}",
            "Reported write capacity units": f"{write_capacity_units:.3f}",
            "Reported base-table write units": f"{table_write_capacity_units:.3f}",
            "Reported GSI write units": f"{gsi_write_capacity_units:.3f}",
        }
        if failure_message:
            details["Message"] = failure_message
        if status in {"INTERRUPTED", "FAILED", "LIMITED", "READ_LIMITED"}:
            details["Resume"] = _resume_text(resume_key)
        write_summary(log_path, details)

    summary = (
        f"read={rows_read:,} examined={rows_examined:,} updated={rows_updated:,} "
        f"changed={rows_changed:,} redundant={redundant_writes:,} "
        f"skipped={rows_skipped:,} errors={errors} "
        f"read_units={read_capacity_units:,.3f} write_units={write_capacity_units:,.3f}"
    )
    if status == "COMPLETED":
        print(f"\nDone. {summary}")
        return 0
    if status == "ABORTED":
        print("\nAborted. No scan or updates were performed.")
        return 0
    if status == "LIMITED":
        print(f"\nStopped at the update limit. {summary}")
        print(f"Resume with: {_resume_text(resume_key)}")
        return 0
    if status == "READ_LIMITED":
        print(f"\nStopped at the row-read limit. {summary}")
        print(f"Resume with: {_resume_text(resume_key)}")
        return 0
    print(f"\n{status.title()}. {failure_message}", file=sys.stderr)
    print(f"Resume with: {_resume_text(resume_key)}", file=sys.stderr)
    return 130 if status == "INTERRUPTED" else 1


if __name__ == "__main__":
    sys.exit(main())
