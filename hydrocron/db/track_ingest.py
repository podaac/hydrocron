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
    SHORTNAME_DICT = {
        "SWOT_L2_HR_RiverSP_reach_2.0": "SWOT_L2_HR_RiverSP_2.0",
        "SWOT_L2_HR_RiverSP_node_2.0": "SWOT_L2_HR_RiverSP_2.0",
        "SWOT_L2_HR_LakeSP_prior_2.0": "SWOT_L2_HR_LakeSP_2.0"
    }

    def __init__(self, collection_shortname, collection_start_date=None, query_start=None, query_end=None):
        """
        :param collection_shortname: Collection shortname to query CMR for
        :type collection-collection_shortname: string
        :param collection_start_date: Date to begin revision_date query in CMR
        :type collection-start_date: datetime
        :param revision_start: Start date to query for granules on
        :type revision_start: datetime
        :param query_start: End date to query for granules on
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
        :type collection-start_date: datetime
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
        """Query Hydrocron for time range and gather GranuleURs that do NOT exist in the Hydrocron table.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param cmr_granules: List of CMR granules to query for
        :type cmr_granules: list
        """

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

    def query_track_ingest(self, hydrocron_track_table, download):
        """Query track status table for granules with "to_ingest" status.

        :param hydrocron_track_table: Name of hydrocron track table to query
        :type hydrocron_track_table: str
        :param download: Whether to store the HTTPS download link
        :type download: bool
        """

        items = self.data_repository.get_status(hydrocron_track_table, "to_ingest")
        logging.info("Located %s granules with 'to_ingest' status.", len(items))

        s3_resource = connection.s3_resource
        for item in items:
            s3_granule_ur = self._query_for_granule_ur(item["granuleUR"], download)
            if s3_granule_ur:
                number_features = count_features(s3_granule_ur,
                                                 s3_resource,
                                                 download,
                                                 self.SHORTNAME_DICT[self.collection_shortname])
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

    def _query_for_granule_ur(self, granule_ur, download):
        """Query CMR for direct S3 access URL.

        Note: Does modify S3 access based on venue.

        :param granule_ur: String Granule UR identifier
        :type granule_ur: str
        :param download: Whether to store the HTTPS download link
        :type download: bool
        """

        query = GranuleQuery()
        granules = query.short_name(self.collection_shortname).readable_granule_name(granule_ur).get_all()
        s3_granule_ur = ""
        for granule in granules:
            links = granule["links"]
            for link in links:
                if download:
                    if link["title"] == f"Download {granule_ur}":
                        if granule_ur == link["href"].split("/")[-1]:
                            s3_granule_ur = link["href"]
                            break
                else:
                    if link["title"] == "This link provides direct download access via S3 to the granule":
                        if granule_ur == link["href"].split("/")[-1]:
                            s3_granule_ur = link["href"]
                            break

        venue = os.getenv("HYDROCRON_ENV").lower()
        if not download and venue in ("sit", "uat"):
            s3_granule_ur = s3_granule_ur.replace("ops", venue)
            logging.info("Retrieving granule from %s venue.", venue.upper())

        return s3_granule_ur

    def publish_cnm_ingest(self):
        """Publish CNM message to trigger granule ingestion."""

    def update_track_ingest(self, hydrocron_track_table):
        """Update track status table with new granules and statuses.

        :param hydrocron_track_table: Name of hydrocron track table to query
        :type hydrocron_track_table: str
        """

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
    download = "download" in event.keys()

    logging.info("Collection shortname: %s", collection_shortname)
    logging.info("Hydrocron table: %s", hydrocron_table)
    logging.info("Hydrocron track ingest table: %s", hydrocron_track_table)
    logging.info("Temporal indicator for revision dates: %s", temporal)
    if temporal:
        logging.info("Temporal start date: %s", query_start)
        logging.info("Temporal end date: %s", query_end)
    else:
        logging.info("Collection start date: %s", collection_start_date)
    logging.info("Download granules indicator: %s", download)

    cmr_granules = track.query_cmr(temporal)
    track.query_hydrocron(hydrocron_table, cmr_granules)
    track.query_track_ingest(hydrocron_track_table, download)
    track.publish_cnm_ingest()
    track.update_track_ingest(hydrocron_track_table)
    if not temporal:
        track.update_runtime()

    logging.info("To Ingest: %s", track.to_ingest)
    logging.info("Ingested: %s", track.ingested)

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))
