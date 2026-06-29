"""Load test data into a local DynamoDB instance for development."""
import os

os.environ['HYDROCRON_ENV'] = 'LOCAL'
os.environ['HYDROCRON_dynamodb_endpoint_url'] = 'http://localhost:8001'
os.environ['AWS_ACCESS_KEY_ID'] = 'fakeMyKeyId'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fakeSecretAccessKey'
os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
os.environ['DEFAULT_RIVER_COLLECTION'] = 'SWOT_L2_HR_RiverSP'
os.environ['DEFAULT_LAKE_COLLECTION'] = 'SWOT_L2_HR_LakeSP'
os.environ['DEFAULT_COLLECTION_VERSION'] = 'D'

from hydrocron.db import HydrocronTable  # noqa: E402
from hydrocron.db.io import swot_shp  # noqa: E402
from hydrocron.utils import connection, constants  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

REACH_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'
)

NODE_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_RiverSP_Node_032_166_SI_20250503T222433_20250503T222608_PIC2_01.zip'
)

LAKE_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_LakeSP_Prior_018_100_GR_20240713T111741_20240713T112027_PIC0_01.zip'
)

# Version D shapefiles
REACH_D_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_RiverSP_Reach_049_058_AU_20260419T185249_20260419T190852_PID0_01.zip'
)

NODE_D_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_RiverSP_Node_046_219_SI_20260221T225751_20260221T230720_PID0_01.zip'
)

LAKE_D_SHAPEFILE = os.path.join(
    DATA_DIR,
    'SWOT_L2_HR_LakeSP_Prior_033_506_AU_20250605T225724_20250605T230824_PID0_01.zip'
)


def create_table(dynamo_resource, table_name, partition_key):
    """Create a DynamoDB table if it doesn't already exist."""
    try:
        table = dynamo_resource.Table(table_name)
        table.load()
        print(f"  Table {table_name} already exists, skipping creation.")
        return
    except dynamo_resource.meta.client.exceptions.ResourceNotFoundException:
        pass

    dynamo_resource.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {'AttributeName': partition_key, 'AttributeType': 'S'},
            {'AttributeName': 'range_start_time', 'AttributeType': 'S'},
            {'AttributeName': 'granuleUR', 'AttributeType': 'S'}
        ],
        KeySchema=[
            {'AttributeName': partition_key, 'KeyType': 'HASH'},
            {'AttributeName': 'range_start_time', 'KeyType': 'RANGE'}
        ],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10},
        GlobalSecondaryIndexes=[{
            "IndexName": "GranuleURIndex",
            "KeySchema": [
                {"AttributeName": "granuleUR", "KeyType": "HASH"},
                {"AttributeName": "range_start_time", "KeyType": "RANGE"}
            ],
            "Projection": {
                "ProjectionType": "INCLUDE",
                "NonKeyAttributes": [partition_key, 'collection_shortname', 'collection_version',
                                     'crid', 'cycle_id', 'pass_id', 'continent_id', 'ingest_time']
            },
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        }]
    )
    print(f"  Created table {table_name}")


def load_shapefile(dynamo_resource, table_name, shapefile_path, columns, partition_key):
    """Load a shapefile into a DynamoDB table."""
    print(f"  Loading {os.path.basename(shapefile_path)} into {table_name}...")
    hydro_table = HydrocronTable(dynamo_resource, table_name)
    items = swot_shp.read_shapefile(shapefile_path, obscure_data=False, columns=columns)
    seen = set()
    deduped = []
    for item in items:
        key = (item[partition_key], item['range_start_time'])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    hydro_table.batch_fill_table(deduped)
    print(f"  Loaded {len(deduped)} items ({len(items) - len(deduped)} duplicates skipped).")


REACH_D_TABLE = 'hydrocron-SWOT_L2_HR_RiverSP_D-reach-table'
NODE_D_TABLE = 'hydrocron-SWOT_L2_HR_RiverSP_D-node-table'
LAKE_D_TABLE = 'hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-table'


def main():
    """Create tables and load test data."""
    dynamo_resource = connection.dynamodb_resource

    print("Creating tables (v2.0)...")
    create_table(dynamo_resource, constants.SWOT_REACH_TABLE_NAME, 'reach_id')
    create_table(dynamo_resource, constants.SWOT_NODE_TABLE_NAME, 'node_id')
    create_table(dynamo_resource, constants.SWOT_PRIOR_LAKE_TABLE_NAME, 'lake_id')

    print("Creating tables (Version D)...")
    create_table(dynamo_resource, REACH_D_TABLE, 'reach_id')
    create_table(dynamo_resource, NODE_D_TABLE, 'node_id')
    create_table(dynamo_resource, LAKE_D_TABLE, 'lake_id')

    print("\nLoading v2.0 data...")
    load_shapefile(dynamo_resource, constants.SWOT_REACH_TABLE_NAME, REACH_SHAPEFILE, constants.REACH_DATA_COLUMNS, 'reach_id')
    load_shapefile(dynamo_resource, constants.SWOT_NODE_TABLE_NAME, NODE_SHAPEFILE, constants.NODE_DATA_COLUMNS, 'node_id')
    load_shapefile(dynamo_resource, constants.SWOT_PRIOR_LAKE_TABLE_NAME, LAKE_SHAPEFILE, constants.PRIOR_LAKE_DATA_COLUMNS, 'lake_id')

    print("\nLoading Version D data...")
    load_shapefile(dynamo_resource, REACH_D_TABLE, REACH_D_SHAPEFILE, constants.REACH_DATA_COLUMNS, 'reach_id')
    load_shapefile(dynamo_resource, NODE_D_TABLE, NODE_D_SHAPEFILE, constants.NODE_DATA_COLUMNS, 'node_id')
    load_shapefile(dynamo_resource, LAKE_D_TABLE, LAKE_D_SHAPEFILE, constants.PRIOR_LAKE_DATA_COLUMNS, 'lake_id')

    print("\nTable row counts:")
    client = dynamo_resource.meta.client
    for table_name in client.list_tables()['TableNames']:
        table = dynamo_resource.Table(table_name)
        table.reload()
        print(f"  {table_name}: {table.item_count} items")

    print("\nDone! Local DynamoDB is ready.")


if __name__ == '__main__':
    main()
