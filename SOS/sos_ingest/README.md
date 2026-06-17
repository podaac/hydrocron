# SOS Discharge Ingest Tool

Ingests SWOT SOS (Sword of Science) discharge results into the Hydrocron DynamoDB reach table. Reads a single SOS NetCDF results file, extracts discharge values per reach and time step across multiple algorithms, matches them to existing DynamoDB rows by finding the closest `range_start_time`, and updates those rows with new SOS discharge columns.

## Setup

```bash
poetry install --with sos
```

## Usage

```bash
poetry run sos_ingest --sos-file <path_to_sos_netcdf_file> [options]
```

## Arguments

| Argument | Default | Description |
|---|---|---|
| `--sos-file` | (required) | Path to SOS NetCDF results file |
| `--table-name` | `hydrocron-swot-reach-table` | DynamoDB table name |
| `--dry-run` | False | Preview mode, no DB writes |
| `--start-reach-id` | None | Reach ID to resume from (skip all IDs before this) |
| `--stop-reach-id` | None | Reach ID to stop after (inclusive) |
| `--time-tolerance` | 900 | Max seconds between SOS time and DB `range_start_time` for a match |
| `--output-dir` | `./output` | Directory for error log and summary report |
| `--algorithms` | `all` | Comma-separated list of algorithms, or `all` |
| `--log-level` | `INFO` | Python logging level |
| `--aws-profile` | (required) | AWS profile name (from ~/.aws/credentials) |
| `--scan-only` | False | Post-ingest verification mode (read-only, no writes) |
| `-y` / `--yes` | False | Skip confirmation prompt |

## Algorithms

The tool processes these discharge algorithms from the SOS file:

| Algorithm | NetCDF Variable | DynamoDB Column |
|---|---|---|
| consensus | `consensus/consensus_q` | `sos_consensus_q` |
| metroman | `metroman/allq` | `sos_metroman_q` |
| momma | `momma/Q` | `sos_momma_q` |
| sic4dvar | `sic4dvar/Q_da` | `sos_sic4dvar_q` |
| sad | `sad/Qa` | `sos_sad_q` |
| hivdi | `hivdi/Q` | `sos_hivdi_q` |
| lakeflow | `lakeflow/q_lakeflow` | `sos_lakeflow_q` |

## Examples

```bash
AF_FILE="/path/to/af_sword_v16_SOS_results_unconstrained_....nc"

# Dry run for a single reach
poetry run sos_ingest \
    --sos-file "$AF_FILE" \
    --dry-run \
    --start-reach-id 18180900091 \
    --stop-reach-id 18180900091

# Live ingest for a single reach
poetry run sos_ingest \
    --sos-file "$AF_FILE" \
    --start-reach-id 18180900091 \
    --stop-reach-id 18180900091

# Process only specific algorithms
poetry run sos_ingest \
    --sos-file "$AF_FILE" \
    --algorithms consensus,sic4dvar

# Post-ingest verification scan
poetry run sos_ingest \
    --sos-file "$AF_FILE" \
    --scan-only

# Script multiple continent files (skip prompts)
for f in /path/to/data/*_sword_v16_SOS_results_*.nc; do
    poetry run sos_ingest --sos-file "$f" -y
done
```

## How It Works

1. Reads the SOS NetCDF file and extracts discharge data per reach per algorithm
2. Filters out fill values (`-999999999999.0`) and invalid times
3. For lakeflow (which has daily resolution), matches each value to the precise SWOT pass time from other algorithms on the same day
4. Shows a pre-flight summary with reach/time step counts and prompts for confirmation
5. For each reach, queries DynamoDB for existing rows
6. Matches SOS timestamps to the closest `range_start_time` within the time tolerance (default 15 minutes)
7. Updates matched rows with discharge columns using `update_item`
8. Skips rows that already have the correct values (idempotent re-runs)
9. Logs errors to a CSV file and writes a summary report

## Time Matching

The SOS file stores time as seconds since `2000-01-01T00:00:00Z`. The tool converts these to datetimes and finds the closest DynamoDB `range_start_time` within the configured tolerance (default 900 seconds / 15 minutes). If no match is found, the time step is logged as `no_match` in the error CSV.

## Resume Capability

If a run is interrupted (Ctrl+C or error), the completion summary shows the last successfully processed `reach_id`. Resume with:

```bash
poetry run sos_ingest --sos-file "$AF_FILE" --start-reach-id <last_reach_id>
```

## Scan Mode

`--scan-only` re-reads the SOS file, queries the DB, and reports discrepancies without writing anything. Useful to verify a previous ingest completed correctly.

## Output Files

Written to `--output-dir` (default `./output`):

- `*_errors_<timestamp>.csv` — per-time-step error log (no_match, no_rows, write_error)
- `*_summary_<timestamp>.txt` — run summary with counts and resume info

## Running Tests

```bash
poetry run pytest SOS/tests/ -v
```
