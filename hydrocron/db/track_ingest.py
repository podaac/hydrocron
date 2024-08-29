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
from hydrocron.db.io.swot_shp import count_features
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
    PAGE_SIZE = 2000

    def __init__(self, collection_shortname, collection_start_date, hydrocron_table):
        self.collection_shortname = collection_shortname
        self.data_repository = DynamoDataRepository(connection.dynamodb_resource)
        self.ingested = []
        self.ssm_client = connection.ssm_client
        self.revision_start = self._get_revision_start(collection_start_date)
        self.revision_end = datetime.datetime.now(timezone.utc)  # TODO - Decide on latency and subtract from current datetime
        self.to_ingest = []

    def _get_revision_start(self, collection_start_date):
        """Locate the last most recent date that was queried in order to only
        query on granules that have not seen before."""

        last_run = self.ssm_client.get_parameter(Name="/service/hydrocron/track-ingest-runtime")["Parameter"]["Value"]
        if last_run != "no_data":
            revision_start = datetime.datetime.strptime(last_run, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            revision_start = None

        if not revision_start:
            revision_start = collection_start_date

        return revision_start

    def query_cmr(self):
        """Query CMR to locate all granules for a specific time range.

        Note: The use of "revision_date" should capture any granules that have
        been reprocessed in the time range.
        """

        query = GranuleQuery()
        logging.info("Querying CMR revision_date range: %s to %s.", self.revision_start, self.revision_end)
        granules = query.short_name(self.collection_shortname).revision_date(self.revision_start, self.revision_end).format("umm_json").get(query.hits())
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
            granule_ur = item["umm"]["GranuleUR"].replace("_swot", "")
            checksum = 0
            for file in item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]:
                if f"{granule_ur}.zip" == file["Name"]:
                    checksum = file["Checksum"]["Value"]
            granule_dict[granule_ur] = {
                "revision_date": item["meta"]["revision-date"],
                "checksum": checksum
            }
        return granule_dict

    def query_hydrocron(self, hydrocron_table, cmr_granules):
        """Query Hydrocron for time range and gather GranuleURs that do NOT exist in the Hydrocron table."""

        for granule_ur, data in cmr_granules.items():
            items = self.data_repository.get_granule_ur(hydrocron_table, f"{granule_ur}.zip")
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

    def query_track_ingest(self, hydrocron_track_table):
        """Query track status table for granules with "to_ingest" status."""

        items = self.data_repository.get_status(hydrocron_track_table, "to_ingest")
        logging.info("Located %s granules with 'to_ingest' status.", len(items))

        s3_resource = connection.s3_resource
        for item in items:
            s3_granule_ur = self._query_for_granule_ur(item["granuleUR"])
            if s3_granule_ur:
                number_features = count_features(s3_granule_ur, s3_resource)
                ingest_item = {
                        "granuleUR": item["granuleUR"],
                        "revision_date": item["revision_date"],
                        "checksum": item["checksum"],
                        "expected_feature_count": int(item["expected_feature_count"]),
                        "actual_feature_count": number_features
                    }
                if number_features == item["expected_feature_count"]:
                    self.ingested.append(ingest_item)
                else:
                    ingest_item["status"] = "to_ingest"
                    self.to_ingest.append(ingest_item)
            else:
                logging.info("Could not locate S3 URL for granule: %s", item["granuleUR"])

        logging.info("Located %s granules that require ingestion.", len(self.to_ingest))
        logging.info("Located %s granules that are already ingested.", len(self.ingested))

    def _query_for_granule_ur(self, granule_ur):
        """Query CMR for direct S3 access URL."""

        query = GranuleQuery()
        granules = query.short_name(self.collection_shortname).readable_granule_name(granule_ur).get_all()
        s3_granule_ur = ""
        for granule in granules:
            links = granule["links"]
            for link in links:
                if link["title"] == "This link provides direct download access via S3 to the granule":
                    if granule_ur == link["href"].split("/")[-1]:
                        s3_granule_ur = link["href"]
                        break
        
        venue = os.getenv("HYDROCRON_ENV").lower()
        if venue == "sit" or venue == "uat":
            s3_granule_ur = s3_granule_ur.replace("ops", venue)
            logging.info("Retrieving granule from %s venue.", venue.upper())
        
        return s3_granule_ur

    def publish_cnm_ingest(self):
        """Publish CNM message to trigger granule ingestion."""

    def update_track_ingest(self, hydrocron_track_table):
        """Update track status table with new granules and statuses."""


def track_ingest_handler(event, context):
    """Lambda handler to track status of ingested granules to Hydrocron."""

    start = datetime.datetime.now()

    logging.info("Context: %s", context)
    logging.info("Event: %s", event)

    collection_shortname = event["collection_shortname"]
    collection_start_date = datetime.datetime.strptime(event["collection_start_date"], "%Y%m%d").replace(tzinfo=timezone.utc)
    hydrocron_table = event["hydrocron_table"]
    hydrocron_track_table = event["hydrocron_track_table"]
    
    logging.info("Collection shortname: %s", collection_shortname)
    logging.info("Collection start date: %s", collection_start_date)
    logging.info("Hydrocron table: %s", hydrocron_table)
    logging.info("Hydrocron track ingest table: %s", hydrocron_track_table)

    track = Track(collection_shortname, collection_start_date, hydrocron_table)
    cmr_granules = track.query_cmr()
    track.query_hydrocron(hydrocron_table, cmr_granules)
    track.query_track_ingest(hydrocron_track_table)
    track.publish_cnm_ingest()
    track.update_track_ingest(hydrocron_track_table)

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))
