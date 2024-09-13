"""
Hydrocron class to track status of ingested granules.
"""

# Standard Imports
import datetime
from datetime import timezone
import json
import logging
import os

# Third-party Imports
from cmr import GranuleQuery

# Application Imports
from hydrocron.api.data_access.db import DynamoDataRepository
from hydrocron.db.load_data import load_data
from hydrocron.utils import connection


logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    level=logging.INFO)


class Track:
    """
    Class to track the status of ingested granules and submit missed or
    newly discovered granules for Hydrocron database ingestion.
    """

    CMR_API = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
    ENV = os.getenv("HYDROCRON_ENV").lower()
    PAGE_SIZE = 2000
    FEATURE_ID = {
        "SWOT_L2_HR_RiverSP_reach_2.0": "reach_id",
        "SWOT_L2_HR_RiverSP_node_2.0": "node_id",
        "SWOT_L2_HR_LakeSP_prior_2.0": "lake_id"
    }
    SHORTNAME = {
        "SWOT_L2_HR_RiverSP_reach_2.0": "SWOT_L2_HR_RiverSP_2.0",
        "SWOT_L2_HR_RiverSP_node_2.0": "SWOT_L2_HR_RiverSP_2.0",
        "SWOT_L2_HR_LakeSP_prior_2.0": "SWOT_L2_HR_LakeSP_2.0"        
    }
    CNM_VERSION = "1.6.0"
    PROVIDER = "JPL-SWOT"

    def __init__(self, collection_shortname, collection_start_date=None, query_start=None, query_end=None):
        """
        :param collection_shortname: Collection shortname to query CMR for
        :type collection_shortname: string
        :param collection_start_date: Date to begin revision_date query in CMR
        :type collection_start_date: datetime
        :param query_start: Start date to query for granules on
        :type query_start: datetime
        :param query_end: End date to query for granules on
        :type query_end: datetime
        """
        self.collection_shortname = collection_shortname
        self.data_repository = DynamoDataRepository(connection.dynamodb_resource)
        self.ingested = []
        self.to_ingest = []
        self.ssm_client = connection.ssm_client
        if collection_start_date:
            self.query_start = self._get_query_start(collection_start_date)
            self.query_end = datetime.datetime.now(timezone.utc)  # TODO - Decide on latency and subtract from current datetime
        else:
            self.query_start = query_start
            self.query_end = query_end

    def _get_query_start(self, collection_start_date):
        """Locate the last most recent date that was queried in order to only
        query on granules that have not seen before.

        :param collection_start_date: Date to begin revision_date query in CMR
        :type collection_start_date: datetime
        """

        last_run = self.ssm_client.get_parameter(Name=f"/service/hydrocron/track-ingest-runtime/{self.collection_shortname}")["Parameter"]["Value"]
        if last_run != "no_data":
            query_start = datetime.datetime.strptime(last_run, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            query_start = None

        if not query_start:
            query_start = collection_start_date

        return query_start

    def query_cmr(self, temporal):
        """Query CMR to locate all granules for a specific time range.

        Note: The use of "revision_date" should capture any granules that have
        been reprocessed in the time range.

        :param temporal: Indicates if temporal search should be conducted
        :type temporal: boolean
        """

        query = GranuleQuery()
        if temporal:
            logging.info("Querying CMR temporal range: %s to %s.", self.query_start, self.query_end)
            granules = query.short_name(self.collection_shortname).temporal(self.query_start, self.query_end).format("umm_json").get(query.hits())
        else:
            logging.info("Querying CMR revision_date range: %s to %s.", self.query_start, self.query_end)
            granules = query.short_name(self.collection_shortname).revision_date(self.query_start, self.query_end).format("umm_json").get(query.hits())
        cmr_granules = {}
        for granule in granules:
            granule_json = json.loads(granule)
            cmr_granules.update(self._get_granule_ur_list(granule_json))
        logging.info("Located %s granules in CMR.", len(cmr_granules.keys()))
        return cmr_granules

    @staticmethod
    def _get_granule_ur_list(granules):
        """Return dict of Granule URs and revision dates from CMR response JSON.

        :param granules: Response JSON dictionary from CMR query
        :type granules: dict

        :rtype: dict
        """

        granule_dict = {}
        for item in granules["items"]:
            granule_ur = item["umm"]["GranuleUR"].replace("_swot", ".zip")
            checksum = 0
            for file in item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]:
                if granule_ur == file["Name"]:
                    checksum = file["Checksum"]["Value"]
            granule_dict[granule_ur] = {
                "revision_date": item["meta"]["revision-date"],
                "checksum": checksum
            }
        return granule_dict

    def query_hydrocron(self, hydrocron_table, cmr_granules):
        """Query Hydrocron for time range and gather GranuleURs that do NOT exist in the Hydrocron table.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param cmr_granules: List of CMR granules to query for
        :type cmr_granules: list
        """

        for granule_ur, data in cmr_granules.items():
            items = self.data_repository.get_granule_ur(hydrocron_table, granule_ur)
            if len(items["Items"]) == 0:
                self.to_ingest.append({
                    "granuleUR": granule_ur,
                    "revision_date": data["revision_date"],
                    "checksum": data["checksum"],
                    "expected_feature_count": -1,
                    "actual_feature_count": 0,
                    "status": "to_ingest"
                })
        logging.info("Located %s granules NOT in Hydrocron.", len(self.to_ingest))

    def query_track_ingest(self, hydrocron_track_table, hydrocron_table):
        """Query track status table for granules with "to_ingest" status.

        :param hydrocron_track_table: Name of hydrocron track table to query
        :type hydrocron_track_table: str
        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        """

        items = self.data_repository.get_status(hydrocron_track_table, "to_ingest")
        logging.info("Located %s granules with 'to_ingest' status.", len(items))

        for item in items:
            granule_ur = item["granuleUR"]
            features = self.data_repository.get_series_granule_ur(
                hydrocron_table,
                self.FEATURE_ID[self.collection_shortname],
                granule_ur
            )
            number_features = len(features)
            ingest_item = {
                "granuleUR": granule_ur,
                "revision_date": item["revision_date"],
                "checksum": item["checksum"],
                "expected_feature_count": int(item["expected_feature_count"]),
                "actual_feature_count": number_features
            }
            if number_features == item["expected_feature_count"]:
                self.ingested.append(ingest_item)
            else:
                ingest_item["status"] = "to_ingest"
                if ingest_item in self.to_ingest:
                    continue    # Skip if not found in Hydrocron table
                self.to_ingest.append(ingest_item)

        logging.info("Located %s granules that require ingestion.", len(self.to_ingest))
        logging.info("Located %s granules that are already ingested.", len(self.ingested))

    def publish_cnm_ingest(self, account_id):
        """Publish CNM message to trigger granule ingestion."""

        cnm_messages = []
        for granule in self.to_ingest:
            granule_ur = granule["granuleUR"]
            cnm_messages.append({
                "identifier": granule_ur.replace(".zip", ""),
                "collection": self.SHORTNAME[self.collection_shortname],
                "provider": self.PROVIDER,
                "version": self.CNM_VERSION,
                "submissionTime": granule["revision_date"],
                "trace": "reproc-hydrocron-track-ingest",
                "product": {
                    "dataVersion": self.collection_shortname.split("_")[-1],
                    "dataProcessingType": "reprocessing",
                    "files": self._query_granule_files(granule_ur)
                }
            })

        sns_client = connection.sns_client
        for cnm_message in cnm_messages:
            sns_client.publish(
                TopicArn = f"arn:aws:sns:us-west-2:{account_id}:svc-hydrocron-{self.ENV}-cnm-response",
                Message = json.dumps(cnm_message),
            )
            logging.info("%s message published to SNS Topic: svc-hydrocron-%s-cnm-response", cnm_message['identifier'], self.ENV)

    def _query_granule_files(self, granule_ur):
        """Query for files metadata.

        :param granule: Name of granule to query for
        :param granule: str
        """

        query = GranuleQuery()
        granules = query.short_name(self.collection_shortname).readable_granule_name(granule_ur).format("umm_json").get_all()
        cnm_files = []
        for granule in granules:
            granule_json = json.loads(granule)
            cnm_file = {}
            for granule_item in granule_json["items"]:
                for granule_file in granule_item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]:
                    if granule_file["Name"] == granule_ur:
                        cnm_file = {
                            "type": "data",
                            "name": granule_ur,
                            "checksumType": granule_file["Checksum"]["Algorithm"].lower(),
                            "checksum": granule_file["Checksum"]["Value"],
                            "size": granule_file["SizeInBytes"]
                        }
                for granule_url in granule_item["umm"]["RelatedUrls"]:
                    if granule_url["Type"] == "GET DATA VIA DIRECT ACCESS":
                        cnm_file["uri"] = granule_url["URL"].replace("ops", self.ENV)
            cnm_files.append(cnm_file)

        return cnm_files

    def update_track_ingest(self, hydrocron_track_table):
        """Update track status table with new granules and statuses.

        :param hydrocron_track_table: Name of hydrocron track table to query
        :type hydrocron_track_table: str
        """

        items = self.ingested + self.to_ingest
        dynamo_resource = connection.dynamodb_resource
        load_data(dynamo_resource=dynamo_resource, table_name=hydrocron_track_table, items=items)
        logging.info("Updated %s with %s items.", hydrocron_track_table, len(items))

    def update_runtime(self):
        """Update SSM parameter runtime for next execution."""

        self.ssm_client.put_parameter(Name=f"/service/hydrocron/track-ingest-runtime/{self.collection_shortname}",
                                      Value=self.query_end.strftime("%Y-%m-%dT%H:%M:%S"),
                                      Overwrite=True)


def track_ingest_handler(event, context):
    """Lambda handler to track status of ingested granules to Hydrocron.

    :param event: Lambda handler Event object
    :type event: dict
    :param context: Lambda handler Context object
    :type context: dict
    """

    start = datetime.datetime.now()

    logging.info("Context: %s", context)
    logging.info("Event: %s", event)

    account_id = context.invoked_function_arn.split(":")[4]
    collection_shortname = event["collection_shortname"]
    hydrocron_table = event["hydrocron_table"]
    hydrocron_track_table = event["hydrocron_track_table"]
    temporal = "temporal" in event.keys()
    if temporal:
        query_start = datetime.datetime.strptime(event["query_start"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        query_end = datetime.datetime.strptime(event["query_end"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        track = Track(collection_shortname, query_start=query_start, query_end=query_end)
    else:
        collection_start_date = datetime.datetime.strptime(event["collection_start_date"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        track = Track(collection_shortname, collection_start_date=collection_start_date)

    logging.info("Collection shortname: %s", collection_shortname)
    logging.info("Hydrocron table: %s", hydrocron_table)
    logging.info("Hydrocron track ingest table: %s", hydrocron_track_table)
    logging.info("Temporal indicator for revision dates: %s", temporal)
    if temporal:
        logging.info("Temporal start date: %s", query_start)
        logging.info("Temporal end date: %s", query_end)
    else:
        logging.info("Collection start date: %s", collection_start_date)

    cmr_granules = track.query_cmr(temporal)
    track.query_hydrocron(hydrocron_table, cmr_granules)
    track.query_track_ingest(hydrocron_track_table, hydrocron_table)
    track.publish_cnm_ingest(account_id)
    track.update_track_ingest(hydrocron_track_table)
    if not temporal:
        track.update_runtime()

    logging.info("To Ingest: %s", track.to_ingest)
    logging.info("Ingested: %s", track.ingested)

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))
