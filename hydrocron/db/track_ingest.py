"""
Hydrocron class to track status of ingested granules.
"""

# Standard Imports
import datetime
from datetime import timezone
import json
import logging
import os
import requests

# Third-party Imports
from cmr import GranuleQuery
from cmr import CMR_UAT

# Application Imports
from hydrocron.api.data_access.db import DynamoDataRepository
from hydrocron.db.load_data import load_data, TableMisMatch
from hydrocron.utils import connection, constants


logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    level=logging.INFO)


class Track:
    """
    Class to track the status of ingested granules and submit missed or
    newly discovered granules for Hydrocron database ingestion.
    """

    BATCH_STATUS = int(os.getenv("BATCH_STATUS")) if os.getenv("BATCH_STATUS") else None
    CMR_API = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
    COUNTER_RANGE = int(os.getenv("COUNTER_RANGE")) if os.getenv("COUNTER_RANGE") else 1
    DEBUG_LOGS = bool(int(os.getenv("DEBUG_LOGS"))) if os.getenv("DEBUG_LOGS") else False
    ENV = os.getenv("HYDROCRON_ENV").lower()
    PAGE_SIZE = 2000
    CNM_VERSION = "1.6.0"
    PROVIDER = "JPL-SWOT"
    SSM_CLIENT = connection.ssm_client
    URS_UAT_TOKEN = "https://uat.urs.earthdata.nasa.gov/api/users/tokens"

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
        if collection_start_date:
            self.query_start = self._get_query_start(collection_start_date)
            self.query_end = datetime.datetime.now(timezone.utc) - datetime.timedelta(hours=1)
        else:
            self.query_start = query_start
            self.query_end = query_end

    def _get_query_start(self, collection_start_date):
        """Locate the last most recent date that was queried in order to only
        query on granules that have not seen before.

        :param collection_start_date: Date to begin revision_date query in CMR
        :type collection_start_date: datetime

        :rtype datetime.datetime
        """

        last_run = self.SSM_CLIENT.get_parameter(Name=f"/service/hydrocron/track-ingest-runtime/{self.collection_shortname}")["Parameter"]["Value"]
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

        :rtype: dict
        """

        query = GranuleQuery()
        query = query.format("umm_json").short_name(constants.SHORTNAME[self.collection_shortname])
        if temporal:
            logging.info("Querying CMR temporal range: %s to %s.", self.query_start, self.query_end)
            query = query.temporal(self.query_start, self.query_end)
        else:
            logging.info("Querying CMR revision_date range: %s to %s.", self.query_start, self.query_end)
            query = query.revision_date(self.query_start, self.query_end)

        if self.ENV in ("sit", "uat"):
            bearer_token = self._get_bearer_token()
            query = query.mode(CMR_UAT).bearer_token(bearer_token)

        granules = query.get(query.hits())
        granules = self._filter_granules(granules)

        cmr_granules = {}
        for granule in granules:
            granule_json = json.loads(granule)
            cmr_granules.update(self._get_granule_ur_list(granule_json))

        logging.info("Located %s granules in CMR.", len(cmr_granules.keys()))
        if self.DEBUG_LOGS is True:
            logging.info("CMR granules located: %s", list(cmr_granules.keys()))
        return cmr_granules

    def _get_bearer_token(self):
        """Get bearer authorizatino token.

        rtype: str
        """

        username = os.getenv("EARTHDATA_USERNAME")
        password = os.getenv("EARTHDATA_PASSWORD")
        get_response = requests.get(self.URS_UAT_TOKEN,
                                    headers={"Accept": "application/json"},
                                    auth=requests.auth.HTTPBasicAuth(username, password),
                                    timeout=30)
        token_data = get_response.json()
        return token_data[0]["access_token"]

    def _filter_granules(self, granules):
        """Filter granules for collection.

        :param granules: List of granules to filter
        :type granules: dict

        :rtype: list
        """

        data_type = self.collection_shortname.split("_")[4].capitalize()
        granule_list = []
        for granule in granules:
            filter_list = []
            granule_json = json.loads(granule)
            for item in granule_json["items"]:
                if data_type in item["meta"]["native-id"]:
                    filter_list.append(item)
            granule_json["hits"] = len(filter_list)
            granule_json["items"] = filter_list
            granule_list.append(json.dumps(granule_json))
        return granule_list

    @staticmethod
    def _get_granule_ur_list(granules):
        """Return dict of Granule URs and revision dates from CMR response JSON.

        :param granules: Response JSON dictionary from CMR query
        :type granules: dict

        :rtype: dict
        """

        granule_dict = {}
        for item in granules["items"]:
            granule_ur = f'{item["umm"]["GranuleUR"].replace("_swot", "")}.zip'
            checksum = 0
            for file in item["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]:
                if granule_ur == file["Name"]:
                    checksum = file["Checksum"]["Value"]
            granule_dict[granule_ur] = {
                "revision_date": item["meta"]["revision-date"],
                "checksum": checksum
            }
        return granule_dict

    def query_hydrocron(self, hydrocron_table, cmr_granules, reprocessed_crid):
        """Query Hydrocron for time range and gather GranuleURs that do NOT exist in the Hydrocron table.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param cmr_granules: List of CMR granules to query for
        :type cmr_granules: list
        :param reprocessed_crid: Collection CRID
        :type reprocessed_crid: string
        """

        for granule_ur, data in cmr_granules.items():
            items = self._query_crid(hydrocron_table, granule_ur, reprocessed_crid)
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

        self.to_ingest = self._remove_duplicates(reprocessed_crid, self.to_ingest)    # Cases where granules with both CRIDs arrive at the same time
        logging.info("Located %s unique CRID granules NOT in Hydrocron after removing duplicates.", len(self.to_ingest))

        self.to_ingest = self._remove_old_products(hydrocron_table, self.to_ingest)    # Cases where there are incremented product counters
        logging.info("Located %s final granules NOT in Hydrocron after product counter filter.", len(self.to_ingest))

        if self.DEBUG_LOGS is True:
            logging.info("Hydrocron granules located: %s", self.to_ingest)

    def _query_crid(self, hydrocron_table, granule_ur, reprocessed_crid):
        """Determine if reprocessing CRID exists and prioritize.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param granule_ur: Granule UR
        :type granule_ur: string
        :param reprocessed_crid: Collection CRID
        :type reprocessed_crid: string

        :rtype: list
        """

        crid = granule_ur.split("_")[-2]
        if crid != reprocessed_crid:    # Cases where forward stream CRID arrives after reprocessed CRID
            reprocessed_granule_ur = granule_ur.replace(crid, reprocessed_crid)
            items = self.data_repository.get_granule_ur(hydrocron_table, reprocessed_granule_ur)
            if self.DEBUG_LOGS is True:
                logging.info("Forward stream: located %s items for reprocessed granule %s.", len(items["Items"]), reprocessed_granule_ur)
            if len(items["Items"]) == 0:    # Check for forward stream CRID
                items = self.data_repository.get_granule_ur(hydrocron_table, granule_ur)
                if self.DEBUG_LOGS is True:
                    logging.info("Forward stream: located %s items for forward stream granule %s.", len(items["Items"]), granule_ur)
        else:    # Cases where reprocessing stream CRID arrives
            items = self.data_repository.get_granule_ur(hydrocron_table, granule_ur)
            if self.DEBUG_LOGS is True:
                logging.info("Reprocessed: located %s items for reprocessed granule %s.", len(items["Items"]), granule_ur)
        return items

    @staticmethod
    def _remove_duplicates(reprocessed_crid, granules_list):
        """Detect duplicate granules with different CRIDs.

        :param reprocessed_crid: Collection CRID
        :type reprocessed_crid: string
        :param granules_list: List of granules to remove duplicates from
        :type granules_list: list

        :rtype list
        """

        # Sort to grab most recent product counter
        granules_list = sorted(granules_list, key=lambda g: g["granuleUR"])

        # Detect duplicates
        duplicate_dict = {}
        for item in granules_list:
            key = "_".join(item["granuleUR"].split("_")[5:8])
            crid = item["granuleUR"].split("_")[-2]
            if key not in duplicate_dict:
                duplicate_dict[key] = {
                    crid: item
                }
            else:
                duplicate_dict[key][crid] = item

        # Remove duplicates
        removed_list = []
        for item in duplicate_dict.values():
            if len(item.keys()) == 2:
                if reprocessed_crid in item.keys():
                    removed_list.append(item[reprocessed_crid])
                else:
                    sorted_crids = dict(sorted(item.items(), reverse=True))
                    removed_list.append(item[next(iter(sorted_crids))])
            if len(item.keys()) == 1:
                removed_list.append(item[next(iter(item))])
        return removed_list

    def _remove_old_products(self, hydrocron_table, granules_list):
        """
        Remove previous product counters from to_ingest list.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param granules_list: List of granules to remove duplicates from
        :type granules_list: list

        :rtype list
        """

        new_products = []
        for granule in granules_list:
            items = self._query_product_counter(hydrocron_table, granule["granuleUR"])
            if len(items["Items"]) == 0:
                new_products.append(granule)
            else:
                if self.DEBUG_LOGS is True:
                    logging.info("Removed old product from to ingest list: %s.", granule["granuleUR"])
        return new_products

    def _query_product_counter(self, hydrocron_table, granule_ur):
        """Determine if reprocessing CRID exists and prioritize.

        If a higher product counter exists, that item is returned indicating the
        older product counter should not be ingested. Otherwise an empty
        list is returned indicating no higher product counters exist.

        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        :param granule_ur: Granule UR
        :type granule_ur: string

        :rtype: list
        """

        product_counter = granule_ur.split("_")[-1].split(".")[0]
        padding = ['0'] * (len(product_counter) - 1)
        items = {
            "Items": []
        }
        for counter in range(int(product_counter), self.COUNTER_RANGE + 1):
            incremented_counter = f"{''.join(padding)}{str(int(counter) + 1)}"
            incremented_granule = granule_ur.replace(f"{product_counter}.zip", f"{incremented_counter}.zip")
            items = self.data_repository.get_granule_ur(hydrocron_table, incremented_granule)
            if len(items["Items"]) > 0:
                logging.info("Located incremented product counter: %s.", incremented_granule)
                break
        return items

    def query_track_ingest(self, hydrocron_track_table, hydrocron_table, reprocessed_crid):
        """Query track status table for granules with "to_ingest" status.

        :param hydrocron_track_table: Name of hydrocron track table to query
        :type hydrocron_track_table: str
        :param hydrocron_table: Name of hydrocron table to query
        :type hydrocron_table: str
        """

        if self.BATCH_STATUS:
            items = self.data_repository.get_status(hydrocron_track_table, "to_ingest", limit=self.BATCH_STATUS)
        else:
            items = self.data_repository.get_status(hydrocron_track_table, "to_ingest")
        logging.info("Located %s granules with 'to_ingest' status.", len(items))
        if self.DEBUG_LOGS is True:
            logging.info("Items located as 'to_ingest' in track ingest: %s", items)

        items = self._remove_duplicates(reprocessed_crid, items)
        logging.info("Located %s unique granules with 'to_ingest' status.", len(items))

        for item in items:
            granule_ur = item["granuleUR"]
            items = self._query_product_counter(hydrocron_table, granule_ur)
            if len(items["Items"]) > 0:
                continue    # Located granule with higher product counter no need to ingest older granule
            features = self.data_repository.get_series_granule_ur(
                hydrocron_table,
                constants.FEATURE_ID[self.collection_shortname],
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
                logging.info("Granule has been ingested: %s - %s features.", ingest_item["granuleUR"], ingest_item["actual_feature_count"])
            else:
                ingest_item["status"] = "to_ingest"
                if ingest_item in self.to_ingest:
                    continue    # Skip if not found in Hydrocron table
                self.to_ingest.append(ingest_item)
                logging.info("Granule needs to be ingested: %s.", ingest_item["granuleUR"])

        if self.DEBUG_LOGS:
            logging.info("Located %s granules that require ingestion before de-duplication.", len(self.to_ingest))
        self.remove_overlap()    # Occurs with granules that have 0 features
        logging.info("Located %s granules that require ingestion.", len(self.to_ingest))
        logging.info("Located %s granules that are already ingested.", len(self.ingested))

    def remove_overlap(self):
        """Remove overlap between to_ingest and ingested.

        This can occur when there are 0 features in a granule and the same
        temporal range is executed on.
        """

        ingested_urs = [granule["granuleUR"] for granule in self.ingested]
        to_ingest = []
        for granule in self.to_ingest:
            if granule["granuleUR"] not in ingested_urs:
                to_ingest.append(granule)
            else:
                logging.info("Removed duplicate that has been ingested: %s.", granule["granuleUR"])
        self.to_ingest = to_ingest

    def publish_cnm_ingest(self, account_id):
        """Publish CNM message to trigger granule ingestion.

        :param account_id: Account number of SNS topic to send CNM
        :type account_id: int
        """

        cnm_messages = []
        for granule in self.to_ingest:
            granule_ur = granule["granuleUR"]
            cnm_messages.append({
                "identifier": granule_ur.replace(".zip", ""),
                "collection": constants.SHORTNAME[self.collection_shortname],
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
                TopicArn=f"arn:aws:sns:us-west-2:{account_id}:svc-hydrocron-{self.ENV}-cnm-response",
                Message=json.dumps(cnm_message)
            )
            if self.DEBUG_LOGS is True:
                logging.info("%s message published to SNS Topic: svc-hydrocron-%s-cnm-response", cnm_message['identifier'], self.ENV)

    def _query_granule_files(self, granule_ur):
        """Query for files metadata.

        :param granule: Name of granule to query for
        :param granule: str

        :rtype: list
        """

        query = GranuleQuery()
        query = query.short_name(constants.SHORTNAME[self.collection_shortname]).readable_granule_name(granule_ur).format("umm_json")

        if self.ENV in ("sit", "uat"):
            bearer_token = self._get_bearer_token()
            query = query.mode(CMR_UAT).bearer_token(bearer_token)

        granules = query.get_all()
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
                        if self.ENV in ("sit", "uat"):
                            cnm_file["uri"] = granule_url["URL"].replace("sit", "uat")
                        else:
                            cnm_file["uri"] = granule_url["URL"]
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

        self.SSM_CLIENT.put_parameter(Name=f"/service/hydrocron/track-ingest-runtime/{self.collection_shortname}",
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
    reprocessed_crid = event["reprocessed_crid"]
    temporal = "temporal" in event.keys()

    parent_collection = constants.SHORTNAME[collection_shortname]
    for table_info in constants.TABLE_COLLECTION_INFO:
        if (table_info['collection_name'] in parent_collection) & (str.lower(table_info['feature_type']) in collection_shortname):
            hydrocron_table = table_info['table_name']
            hydrocron_track_table = table_info['track_table']
            break
    else:
        raise TableMisMatch(f"Error: Cannot query data for tables: '{hydrocron_table}' and '{hydrocron_track_table}'")

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
    logging.info("Reprocessed CRID: %s", reprocessed_crid)
    logging.info("Environment: %s", track.ENV.upper())

    cmr_granules = track.query_cmr(temporal)
    track.query_hydrocron(hydrocron_table, cmr_granules, reprocessed_crid)
    track.query_track_ingest(hydrocron_track_table, hydrocron_table, reprocessed_crid)
    track.publish_cnm_ingest(account_id)
    track.update_track_ingest(hydrocron_track_table)
    if not temporal:
        track.update_runtime()

    if track.DEBUG_LOGS is True:
        logging.info("To Ingest: %s", track.to_ingest)
        logging.info("Ingested: %s", track.ingested)

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))
