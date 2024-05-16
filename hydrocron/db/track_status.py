"""
Hydrocron class to track status of ingested granules.

Note: Current usage uses a JSON file as a substitute for a DynamoDB table and 
queries that JSON file to determine what has been ingested. If this is 
implemented we should query the Hydrocron reaches and nodes tables.
"""

# Standard Imports
import datetime
import json
import logging
import pathlib

# Third-party Imports
import requests


TMP_WORKSPACE = pathlib.Path("/path/to/store/track/data")
TMP_WORKSPACE.mkdir(parents=True, exist_ok=True)


logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(filename=f"{TMP_WORKSPACE}/track.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    level=logging.DEBUG)


class Track:
    """
    Class to track the status of ingested granules and submit missed or 
    newly discovered granules for Hydrocron database ingestion.
    """

    CMR_API = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
    COLLECTION_START_DATE = datetime.datetime(2022, 12, 16)
    PAGE_SIZE = 2000
    SHORTNAME = "SWOT_L2_HR_RiverSP_2.0"

    def __init__(self):

        self.cmr_granules = {}
        self.hydrocron_granules = {}
        self.revision_start = self._get_revision_start()
        self.revision_end = datetime.datetime.now()

    def _get_revision_start(self):
        """Locate the last most recent date that was queried in order to only
        query on granules that have not seen before."""

        with open(f"{TMP_WORKSPACE}/track.json", encoding="utf-8") as json_file:
            track_data = json.load(json_file)

        if not track_data:
            revision_start = self.COLLECTION_START_DATE

        else:
            revision_start = max(datetime.datetime.strptime(granule["revision_date"], "%Y-%m-%dT%H:%M:%S.%fZ") for granule in track_data.values())

        return revision_start

    def query_cmr(self):
        """Query CMR to locate all granules for a specific time range.

        Note: The use of "revision_date" should capture any granules that have
        been reprocessed in the time range.
        """

        temporal_range = f"{self.revision_start.strftime('%Y-%m-%dT%H:%M:%SZ')},{self.revision_end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        parameters = {
            "short_name": self.SHORTNAME,
            "revision_date": temporal_range,
            "page_size": self.PAGE_SIZE
        }
        logging.info("Search URL: %s", self.CMR_API)
        logging.info("Search Parameters: %s", parameters)
        cmr_response = requests.get(url=self.CMR_API, params=parameters, timeout=30)
        hits = cmr_response.headers["CMR-Hits"]
        self.cmr_granules = self._get_granule_ur_list(cmr_response.json())
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
            granule_dict[item["umm"]["GranuleUR"]] = item["meta"]["revision-date"]
        return granule_dict

    def query_hydrocron(self):
        """Query Hydrocron river and node tables for time range and gather GranuleURs."""

        with open(f"{TMP_WORKSPACE}/track.json", encoding="utf-8") as json_file:
            track_data = json.load(json_file)

        if track_data:
            for key, value in track_data.items():
                db_date = datetime.datetime.strptime(value["revision_date"], "%Y-%m-%dT%H:%M:%S.%fZ")
                if self.revision_start <= db_date <= self.revision_end:
                    self.hydrocron_granules[key] = value
                status = value["status"]
                if status == "to_ingest":
                    self.hydrocron_granules[key] = value

        logging.info("Located %s granules in Hydrocron.", len(self.hydrocron_granules.keys()))

    def track_status(self):
        """Track status of ingested granules and create a list of granules to be
        ingested.
        """

        # Determine what has been ingested but has a to_ingest status
        overlap_keys = [overlap for overlap in self.hydrocron_granules if overlap in self.cmr_granules]
        count_ingested = 0
        for key in overlap_keys:
            if self.hydrocron_granules[key]["revision_date"] != self.cmr_granules[key]:
                continue    # Need to ingest the granule again as it may have change since last run
            if self.hydrocron_granules[key]["status"] == "to_ingest":
                self.hydrocron_granules[key] = {
                    "status": "ingested",
                    "revision_date": self.cmr_granules[key]
                }
                count_ingested += 1
        logging.info("Set %s granules' status to 'ingested'.", count_ingested)

        # Determine what hasn't been ingested
        cmr_keys = [cmr_key for cmr_key in self.cmr_granules if cmr_key not in self.hydrocron_granules]
        for key in cmr_keys:
            self.hydrocron_granules[key] = {
                "status": "to_ingest",
                "revision_date": self.cmr_granules[key]
            }
        logging.info("Set %s granules' status to 'to_ingest'.", len(cmr_keys))

        # Update database
        with open(f"{TMP_WORKSPACE}/track.json", encoding="utf-8") as json_file:
            hydrocron_granules = json.load(json_file)
        hydrocron_granules.update(self.hydrocron_granules)
        with open(f"{TMP_WORKSPACE}/track.json", 'w', encoding="utf-8") as json_file:
            json.dump(hydrocron_granules, json_file, indent=2)

        # Report on granules that have been set to to_ingest
        to_ingest = {key:value for key,value in self.hydrocron_granules.items() if value["status"] == "to_ingest"}
        with open(f"{TMP_WORKSPACE}/granule_toingest_{self.revision_end.strftime('%Y%m%dT%H%M%S')}.json", 'w', encoding="utf-8") as json_file:
            json.dump(to_ingest, json_file, indent=2)

        # Report on granules that have been set to ingested
        ingested = {key:value for key,value in self.hydrocron_granules.items() \
            if value["status"] == "ingested" and \
            datetime.datetime.strptime(value["revision_date"], "%Y-%m-%dT%H:%M:%S.%fZ") != self.revision_start}
        with open(f"{TMP_WORKSPACE}/granule_ingested_{self.revision_end.strftime('%Y%m%dT%H%M%S')}.json", 'w', encoding="utf-8") as json_file:
            json.dump(ingested, json_file, indent=2)


def track_status_handler(event, context):
    """Lambda handler to track status of ingested granules to Hydrocron."""

    start = datetime.datetime.now()

    logging.info("Context: %s", context)
    logging.info("Event: %s", event)

    track = Track()
    track.query_cmr()
    track.query_hydrocron()
    track.track_status()

    end = datetime.datetime.now()
    logging.info("Elapsed: %s", (end - start))


if __name__ == "__main__":
    track_status_handler(None, None)
