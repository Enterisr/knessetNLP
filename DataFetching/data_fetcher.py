import requests
import os
import json
from urllib.parse import urlparse
import re
import requests_cache
from subprocess import run
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from DataFetching.PartitionHandler import PartitionHandler
from logger_config import get_logger


class KnessetDataFetcher:
    """
    A class for fetching and processing Knesset committee data.
    """

    # Class constants
    CACHE_FILE = "knesset_cache.sqlite"
    TEMP_RESOURCE_FOLDER = "temp"
    OUTPUT_FOLDER = "committee_data"
    FILE_BUFFER_SIZE = 8192
    COMMITTEE_SESSION_STR = "KNS_DocumentCommitteeSession"
    COMMITTEE_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/?committee_id"
    COMMITTEE_SESSION_COUNT_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_CommitteeSession?$filter=KnessetNum eq ~knesset_num~ &$count=true&$top=0"
    COMMITTEES_DATA_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_Committee?committee_id"
    MAX_CAST_TRIES_FOR_DOC = 10

    def __init__(self, knesset_num: int, force_refresh: bool = False, to_save_txt: bool = False):
        """
        Initialize the KnessetDataFetcher.

        Args:
            knesset_num (int): The Knesset number to fetch data for
            force_refresh (bool): Whether to force refresh existing files
            to_save_txt (bool): Whether to save text files after processing
        """
        self.knesset_num = knesset_num
        self.force_refresh = force_refresh
        self.to_save_txt = to_save_txt
        self.committees = {}
        self.mks = {}

        self.partition_handler = PartitionHandler()
        self.logger = get_logger(__name__)

        # Install cache
        requests_cache.install_cache(
            self.CACHE_FILE,
            backend='sqlite',
            expire_after=3600
        )

        # Initialize folders and data
        self._init_folders()
        self._load_committees_data()

    def _init_folders(self):
        """Initialize required folders."""
        os.makedirs(self.TEMP_RESOURCE_FOLDER, exist_ok=True)
        os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)

    def _load_committees_data(self):
        """Load committees data from the API."""
        response = requests.get(self.COMMITTEES_DATA_URI)
        committees_list = response.json()['value']
        for c in committees_list:
            self.committees[c["Id"]] = c

    def read_doc_as_txt(self, doc: str) -> str:
        """Convert document to text using LibreOffice."""
        # todo: install on setup+move to docker
        cmd = [
            "soffice.com",
            "--convert-to",
            "txt:Text (encoded):UTF8",
            "--outdir",
            self.TEMP_RESOURCE_FOLDER,
            doc,
        ]
        run(cmd, check=True)

        doc_path = Path(doc)
        txt_doc_path = doc_path.stem + ".txt"
        output_file = Path(os.path.join(
            self.TEMP_RESOURCE_FOLDER, txt_doc_path))

        with open(output_file, "r", encoding="utf-8") as f:
            text_content = f.read()

        if not self.to_save_txt:
            output_file.unlink(missing_ok=True)

        return text_content

    def extract_json_path(self, meta: dict) -> str:
        """Extract JSON file path for saving document."""
        doc_id = Path(urlparse(meta["FilePath"]).path).stem
        folder = os.path.join(self.OUTPUT_FOLDER,
                              self.partition_handler.get_folder())

        os.makedirs(folder, exist_ok=True)

        output_path = os.path.join(
            folder, f"{doc_id}.json")
        return output_path

    def save_doc_as_json(self, text: str, meta: dict, out_path: str):
        """Save document text and metadata as JSON."""
        doc_id = Path(urlparse(meta["FilePath"]).path).stem
        committee_name = meta.get(
            "CommitteeName", "unknown_committee").strip().replace(" ", "_")
        date = meta.get("SessionDate", None)

        data = {
            "knesset_num": self.knesset_num,
            "committee": committee_name,
            "doc_id": doc_id,
            "date": date,
            "source_file": meta["FilePath"],
            "text": text
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def read_resource_from_remote(self, uri: str) -> str:
        """Download resource from remote URI and save locally."""
        cleaned_url = re.sub(r'(?<!:)//', '/', uri)

        with requests_cache.disabled():
            response = requests.get(cleaned_url)

        file_name = os.path.basename(urlparse(cleaned_url).path)
        current_path = os.path.join(self.TEMP_RESOURCE_FOLDER, file_name)

        with open(current_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.FILE_BUFFER_SIZE):
                if chunk:
                    f.write(chunk)
        return os.path.abspath(current_path)

    def remove_resource_after_reading(self, doc_path: str) -> bool:
        """Remove temporary resource file after processing."""
        if os.path.exists(doc_path):
            try:
                os.remove(doc_path)
                return True
            except OSError as e:
                self.logger.error(f"Error removing file {doc_path}: {e}")
        return False

    def process_document(self, doc: dict, committee_name: str, date: str, tries: int = 0):
        """Process a single document - download, convert to text, and save as JSON."""
        doc["CommitteeName"] = committee_name
        doc["SessionDate"] = date
        doc_path = ""
        try:
            out_path = self.extract_json_path(doc)
            if self.force_refresh or not os.path.exists(out_path):
                doc_path = self.read_resource_from_remote(doc["FilePath"])
                text = self.read_doc_as_txt(doc_path)
                self.save_doc_as_json(text, doc, out_path)
        except Exception as e:
            if tries < self.MAX_CAST_TRIES_FOR_DOC:
                self.logger.info(
                    f"Error processing {doc['FilePath']}, Trying Again. {e}")
                self.process_document(doc, committee_name, date, tries=tries+1)
            else:
                self.logger.error(
                    f"Error processing {doc['FilePath']} OUT OF TRIES")
        finally:
            self.remove_resource_after_reading(doc_path)

    def fetch_mks_data(self) -> dict:
        """Fetch MK (Members of Knesset) data for the specified Knesset number."""
        uri_for_person_id = f"""https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_PersonToPosition?
        $filter=KnessetNum%20eq%20{self.knesset_num}%20
        and%20FactionName%20ne%20null&$expand=KNS_Person"""
        res = requests.get(uri_for_person_id)
        mks_list = res.json()['value']
        for mk in mks_list:
            self.mks[mk["PersonID"]] = {
                "Id": mk["KNS_Person"]["Id"],
                # save only first name,
                "FirstName": mk["KNS_Person"]["FirstName"],
                "Email": mk["KNS_Person"]["Email"],
                "LastName": mk["KNS_Person"]["LastName"],
                "FactionName": mk["FactionName"],
                "FactionID": mk["FactionID"],
            }

        # Save MKs data to a JSON file for reference
        self.save_mks_to_file(self.mks)
        return self.mks

    def save_mks_to_file(self, mks_data: dict, file_path: str = "mks_data.json"):
        """
        Save the MKs data to a JSON file for reference by other modules.

        Args:
            mks_data (dict): Dictionary containing MKs data
            file_path (str): Path where the JSON file will be saved
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mks_data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"MKs data saved to {file_path}")

    def fetch_all_committees_from_knesset(self):
        """Fetch all committee data from the specified Knesset."""
        # TODO: figure out threads here
        # Add debug parameter with default False
        debug = os.getenv('DEBUG', 'false').lower() == 'true'

        page_size = 50
        skip = 0

        while True:
            self.logger.debug(
                f"Fetching committee sessions from Knesset {self.knesset_num}: skip={skip}, limit={page_size}")

            is_end = self.fetch_paginated_committees_from_knesset(
                page_size, skip)

            if not is_end or debug:
                break

            skip += page_size

        if debug:
            self.logger.info("Debug mode: Only fetched first page")

    def build_committees_uri(self, top: int, skip: int) -> str:
        """Build URI for fetching committee data with pagination."""
        expand_part = "$expand=KNS_CmtSessionItem%2CKNS_DocumentCommitteeSession"
        filter_part = f"$filter=KnessetNum%20eq%20{self.knesset_num}"
        pagination_part = f"$top={top}&$skip={skip}&$orderby=ID"
        return f"https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_CommitteeSession?{filter_part}&{expand_part}&{pagination_part}"

    def fetch_paginated_committees_from_knesset(self, top: int, skip: int) -> bool:
        """Fetch a paginated batch of committee data."""
        uri = self.build_committees_uri(top, skip)
        response = requests.get(uri)
        committees_data = response.json()['value']
        if len(committees_data) == 0:
            return False

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for session in committees_data:
                committee_name = self.committees[session["CommitteeID"]].get(
                    "Name", "unknown_committee")
                date = session.get("StartDate", None)

                if self.COMMITTEE_SESSION_STR in session:
                    for doc in session[self.COMMITTEE_SESSION_STR]:
                        if doc['ApplicationDesc'] == 'DOC' and doc["GroupTypeID"] == 23:
                            futures.append(executor.submit(
                                self.process_document, doc, committee_name, date))

            for future in as_completed(futures):
                future.result()

        return True

    def process_knesset_data(self):
        """Main method to process all Knesset data."""
        self.fetch_mks_data()
        self.fetch_all_committees_from_knesset()


if __name__ == "__main__":
    # Create fetcher instance and process data
    main_fetcher = KnessetDataFetcher(knesset_num=25)
    main_fetcher.process_knesset_data()
