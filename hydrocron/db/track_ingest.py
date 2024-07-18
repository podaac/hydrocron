"""
Hydrocron class to track status of ingested granules.
"""

# Standard Imports
import datetime
from datetime import timezone
import logging

# Third-party Imports
import requests

# Application Imports
from hydrocron.api.data_access.db import DynamoDataRepository
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
        self.cmr_granules = {}
        self.hydrocron_granules = {}
        self.hydrocron_table = hydrocron_table
        self.revision_start = self._get_revision_start(collection_start_date)
        self.revision_end = datetime.datetime.now(timezone.utc)  # TODO - Decide on latency and subtract from current datetime

    def _get_revision_start(self, collection_start_date):
        """Locate the last most recent date that was queried in order to only
        query on granules that have not seen before."""

        # TODO - Query track-ingest table to determine max revision date
        revision_start = None

        if not revision_start:
            revision_start = collection_start_date

        return revision_start

    def query_cmr(self):
        """Query CMR to locate all granules for a specific time range.

        Note: The use of "revision_date" should capture any granules that have
        been reprocessed in the time range.
        """

        temporal_range = f"{self.revision_start.strftime('%Y-%m-%dT%H:%M:%SZ')},{self.revision_end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        parameters = {
            "short_name": self.collection_shortname,
            "revision_date": temporal_range,
            "page_size": self.PAGE_SIZE
        }
        logging.info("Search URL: %s", self.CMR_API)
        logging.info("Search Parameters: %s", parameters)
        cmr_response = requests.get(url=self.CMR_API, params=parameters, timeout=30)
        self.cmr_granules = self._get_granule_ur_list(cmr_response.json())

        hits = cmr_response.headers["CMR-Hits"]
        total = len(self.cmr_granules.keys())

        if "CMR-Search-After" in cmr_response.headers.keys():
            search_after = cmr_response.headers["CMR-Search-After"]
        else:
            search_after = ""

        headers = {}
        while search_after:
            logging.info("Searching for more results...%s out of %s", total, hits)
            headers["CMR-Search-After"] = search_after
            cmr_response = requests.get(url=self.CMR_API, headers=headers, params=parameters, timeout=30)
            self.cmr_granules.update(self._get_granule_ur_list(cmr_response.json()))
            total = len(self.cmr_granules.keys())
            if "CMR-Search-After" in cmr_response.headers.keys():
                search_after = cmr_response.headers["CMR-Search-After"]
            else:
                search_after = ""

        for granule, revision_date in self.cmr_granules.items():
            logging.debug("CMR granule located: %s  -  %s", granule, revision_date)
        logging.info("Located %s granules in CMR.", len(self.cmr_granules.keys()))

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

    def query_hydrocron(self):
        """Query Hydrocron for time range and gather GranuleURs."""

        data_repository = DynamoDataRepository(connection.dynamodb_resource)
        for granule_ur, data in self.cmr_granules.items():
            items = data_repository.get_granule_ur(self.hydrocron_table, f"{granule_ur}.zip")
            if len(items["Items"]) > 0:
                self.hydrocron_granules[granule_ur] = data

        logging.info("Located %s granules in Hydrocron.", len(self.hydrocron_granules.keys()))

    def query_track_ingest(self):
        """Query track status table for granules with "to_ingest" status."""

    def count_features(self):
        """Count granule features to determine if all features have been ingested."""

    def publish_cnm_ingest(self):
        """Publish CNM message to trigger granule ingestion."""

    def update_track_ingest(self):
        """Update track status table with new granules and statuses."""


def track_ingest_handler(event, context):
    """Lambda handler to track status of ingested granules to Hydrocron."""

    start = datetime.datetime.now()

    logging.info("Context: %s", context)
    logging.info("Event: %s", event)

    collection_shortname = event["collection_shortname"]
    collection_start_date = datetime.datetime.strptime(event["collection_start_date"], "%Y%m%d").replace(tzinfo=timezone.utc)
    hydrocron_table = event["hydrocron_table"]

    track = Track(collection_shortname, collection_start_date, hydrocron_table)
    track.query_cmr()
    track.query_hydrocron()
    track.query_track_ingest()
    track.count_features()
    track.publish_cnm_ingest()
    track.update_track_ingest()

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))
