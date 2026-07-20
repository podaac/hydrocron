"""Shared fixtures for SOS ingest tests."""
import os
import tempfile

import boto3
import moto
import numpy as np
import pytest
from netCDF4 import Dataset

from SOS.sos_ingest.config import IngestConfig

# Sample time values (seconds since 2000-01-01)
SAMPLE_TIMES = [748617713.0, 750420415.0, 750892839.0, 752223121.0]
MISSING_TIME = -999999999999.0
MISSING_DISCHARGE = -999999999999.0

# Sample discharge values per reach (same pattern for each algorithm, scaled slightly)
DISCHARGE_DATA = {
    0: [MISSING_DISCHARGE],
    1: [MISSING_DISCHARGE, 28.95, 21.86, 45.12],
    2: [MISSING_DISCHARGE, 18.97, 12.31, 33.44],
    3: [52.08, 29.30, 10.93],
    4: [104.65, 123.21],
}

REACH_IDS = [10000000011, 10000000021, 10000000031, 10000000041, 10000000051]

# Time arrays per reach
TIME_DATA = {
    0: [SAMPLE_TIMES[0]],
    1: SAMPLE_TIMES[:4],
    2: [SAMPLE_TIMES[0], SAMPLE_TIMES[1], MISSING_TIME, SAMPLE_TIMES[3]],
    3: SAMPLE_TIMES[:3],
    4: SAMPLE_TIMES[:2],
}


@pytest.fixture()
def sample_sos_netcdf():
    """Create a mini SOS NetCDF file with VLen arrays matching real file structure."""
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filepath = tmp.name

    ds = Dataset(filepath, "w", format="NETCDF4")
    try:
        vlen_float = ds.createVLType(np.float64, "vlen_float")
        vlen_int = ds.createVLType(np.int64, "vlen_int")

        ds.createDimension("num_reaches", len(REACH_IDS))

        # reaches group
        reaches_grp = ds.createGroup("reaches")
        reach_id_var = reaches_grp.createVariable("reach_id", np.int64, ("num_reaches",))
        reach_id_var[:] = np.array(REACH_IDS, dtype=np.int64)

        time_var = reaches_grp.createVariable("time", vlen_float, ("num_reaches",))
        time_var.missing_value = MISSING_TIME
        for i, times in TIME_DATA.items():
            time_var[i] = np.array(times, dtype=np.float64)

        # consensus group
        consensus_grp = ds.createGroup("consensus")
        cq_var = consensus_grp.createVariable("consensus_q", vlen_float, ("num_reaches",))
        cq_var.missing_value = MISSING_DISCHARGE
        for i, vals in DISCHARGE_DATA.items():
            cq_var[i] = np.array(vals, dtype=np.float64)

        time_int_var = consensus_grp.createVariable("time_int", vlen_int, ("num_reaches",))
        time_int_var.missing_value = np.int64(-999999999999)
        for i, times in TIME_DATA.items():
            time_int_var[i] = np.array(times, dtype=np.int64)

        # metroman group — BUG: missing_value attr is nan but actual fill is -999999999999.0
        metro_grp = ds.createGroup("metroman")
        mq_var = metro_grp.createVariable("allq", vlen_float, ("num_reaches",))
        mq_var.missing_value = np.nan  # BUG in real data
        for i, vals in DISCHARGE_DATA.items():
            scaled = [v * 1.1 if v != MISSING_DISCHARGE else MISSING_DISCHARGE for v in vals]
            mq_var[i] = np.array(scaled, dtype=np.float64)

        # momma group
        momma_grp = ds.createGroup("momma")
        momq_var = momma_grp.createVariable("Q", vlen_float, ("num_reaches",))
        momq_var.missing_value = MISSING_DISCHARGE
        for i, vals in DISCHARGE_DATA.items():
            scaled = [v * 0.9 if v != MISSING_DISCHARGE else MISSING_DISCHARGE for v in vals]
            momq_var[i] = np.array(scaled, dtype=np.float64)

        # sic4dvar group
        sic4dvar_grp = ds.createGroup("sic4dvar")
        s4_var = sic4dvar_grp.createVariable("Q_da", vlen_float, ("num_reaches",))
        s4_var.missing_value = MISSING_DISCHARGE
        for i, vals in DISCHARGE_DATA.items():
            scaled = [v * 1.2 if v != MISSING_DISCHARGE else MISSING_DISCHARGE for v in vals]
            s4_var[i] = np.array(scaled, dtype=np.float64)

        # sad group
        sad_grp = ds.createGroup("sad")
        sq_var = sad_grp.createVariable("Qa", vlen_float, ("num_reaches",))
        sq_var.missing_value = MISSING_DISCHARGE
        for i, vals in DISCHARGE_DATA.items():
            scaled = [v * 0.8 if v != MISSING_DISCHARGE else MISSING_DISCHARGE for v in vals]
            sq_var[i] = np.array(scaled, dtype=np.float64)

        # hivdi group — BUG: no missing_value attribute at all
        hivdi_grp = ds.createGroup("hivdi")
        hq_var = hivdi_grp.createVariable("Q", vlen_float, ("num_reaches",))
        # Intentionally NO missing_value attribute
        for i, vals in DISCHARGE_DATA.items():
            scaled = [v * 1.05 if v != MISSING_DISCHARGE else MISSING_DISCHARGE for v in vals]
            hq_var[i] = np.array(scaled, dtype=np.float64)

        # lakeflow group — fixed 2D array with shared 1D time axis
        num_lakeflow_dates = 4
        lakeflow_grp = ds.createGroup("lakeflow")
        ds.createDimension("lakeflow_dates", num_lakeflow_dates)

        # Shared time axis: daily times corresponding to the same days as SAMPLE_TIMES
        # but truncated to midnight (daily resolution)
        lakeflow_day_times = []
        for t in SAMPLE_TIMES:
            day_seconds = int(t) - (int(t) % 86400)
            lakeflow_day_times.append(day_seconds)
        lf_time_var = lakeflow_grp.createVariable("lakeflow_date", np.int64, ("lakeflow_dates",), fill_value=np.int64(-999999999999))
        lf_time_var[:] = np.array(lakeflow_day_times, dtype=np.int64)

        lf_q_var = lakeflow_grp.createVariable("q_lakeflow", np.float64, ("num_reaches", "lakeflow_dates"), fill_value=MISSING_DISCHARGE)
        # Fill with fill value first, then set valid data
        lf_q_data = np.full((len(REACH_IDS), num_lakeflow_dates), MISSING_DISCHARGE, dtype=np.float64)
        # Reach 0: all fill (no valid data)
        # Reach 1: valid at indices 1, 2, 3
        lf_q_data[1, 1] = 15.5
        lf_q_data[1, 2] = 22.3
        lf_q_data[1, 3] = 18.7
        # Reach 2: valid at index 1, NaN at index 2
        lf_q_data[2, 1] = 9.8
        lf_q_data[2, 2] = np.nan
        # Reach 3: valid at indices 0, 1
        lf_q_data[3, 0] = 44.2
        lf_q_data[3, 1] = 31.6
        # Reach 4: valid at index 0
        lf_q_data[4, 0] = 88.9
        lf_q_var[:] = lf_q_data

    finally:
        ds.close()

    yield filepath
    os.unlink(filepath)


MOCK_TABLE_NAME = "hydrocron-swot-reach-table"
MOCK_REACH_ID = "18180900091"
MOCK_REACH_TIMES = [
    "2023-09-15T10:00:00Z",
    "2023-09-25T14:30:00Z",
    "2023-10-05T08:15:00Z",
]


@pytest.fixture()
def mock_dynamodb_table():
    """Create a moto-mocked DynamoDB table pre-populated with sample reach rows."""
    with moto.mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        dynamodb.create_table(
            TableName=MOCK_TABLE_NAME,
            AttributeDefinitions=[
                {"AttributeName": "reach_id", "AttributeType": "S"},
                {"AttributeName": "range_start_time", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "reach_id", "KeyType": "HASH"},
                {"AttributeName": "range_start_time", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table = dynamodb.Table(MOCK_TABLE_NAME)

        # Add sample rows
        for t in MOCK_REACH_TIMES:
            table.put_item(Item={
                "reach_id": MOCK_REACH_ID,
                "range_start_time": t,
                "time": "748617713.0",
                "wse": "286.30",
            })

        # Add a fill-value row that should be filtered out
        table.put_item(Item={
            "reach_id": MOCK_REACH_ID,
            "range_start_time": "1900-01-01T00:00:00Z",
            "time": "-999999999999.0",
        })

        # Add a reach with no valid rows (only fill)
        table.put_item(Item={
            "reach_id": "99999999999",
            "range_start_time": "1900-01-01T00:00:00Z",
            "time": "-999999999999.0",
        })

        yield dynamodb


@pytest.fixture()
def sample_config(sample_sos_netcdf):
    """Return an IngestConfig with dry_run=True and reasonable test defaults."""
    return IngestConfig(
        sos_file=sample_sos_netcdf,
        aws_profile=None,
        table_name=MOCK_TABLE_NAME,
        dry_run=True,
        output_dir=tempfile.mkdtemp(),
    )
