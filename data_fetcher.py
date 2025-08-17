import requests
import os
import json
from urllib.parse import urlparse
import re
import requests_cache
from subprocess import run
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_FILE = "knesset_cache.sqlite"
TEMP_RESOURCE_FOLDER = "temp"
OUTPUT_FOLDER = "committee_data"
FILE_BUFFER_SIZE = 8192
COMMITTEE_SESSION_STR = "KNS_DocumentCommitteeSession"
COMMITTEE_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/?committee_id"
COMMITTEE_SESSION_COUNT_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_CommitteeSession?$filter=KnessetNum eq ~knesset_num~ &$count=true&$top=0"
COMMITTEES_DATA_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_Committee?committee_id"

requests_cache.install_cache(CACHE_FILE, backend='sqlite', expire_after=3600)
MAX_CAST_TRIES_FOR_DOC = 10
COMMITTEES = {}
MKS = {}
SAVE_TXT = os.getenv('SAVE_TXT', 'false').lower() == 'true'


def read_doc_as_txt(doc: str):
    # todo: install on setup+move to docker
    cmd = [
        "soffice.com",
        "--convert-to",
        "txt:Text (encoded):UTF8",
        "--outdir",
        TEMP_RESOURCE_FOLDER,
        doc,
    ]
    run(cmd, check=True)

    doc_path = Path(doc)
    txt_doc_path = doc_path.stem + ".txt"
    output_file = Path(os.path.join(TEMP_RESOURCE_FOLDER, txt_doc_path))

    with open(output_file, "r", encoding="utf-8") as f:
        text_content = f.read()

    if not SAVE_TXT:
        output_file.unlink(missing_ok=True)

    return text_content


def extract_json_path(meta: dict, output_dir: str,):
    doc_id = Path(urlparse(meta["FilePath"]).path).stem
    output_path = os.path.join(output_dir, f"{doc_id}.json")
    return output_path


def save_doc_as_json(text: str, meta: dict, knesset_num: int, out_path: str):
    doc_id = Path(urlparse(meta["FilePath"]).path).stem
    committee_name = meta.get(
        "CommitteeName", "unknown_committee").strip().replace(" ", "_")
    date = meta.get("SessionDate", None)

    data = {
        "knesset_num": knesset_num,
        "committee": committee_name,
        "doc_id": doc_id,
        "date": date,
        "source_file": meta["FilePath"],
        "text": text
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_committees_data():
    response = requests.get(COMMITTEES_DATA_URI)
    committees_list = response.json()['value']
    for c in committees_list:
        COMMITTEES[c["Id"]] = c
    return COMMITTEES


def read_resource_from_remote(uri: str):
    cleaned_url = re.sub(r'(?<!:)//', '/', uri)

    with requests_cache.disabled():
        response = requests.get(cleaned_url)

    file_name = os.path.basename(urlparse(cleaned_url).path)
    current_path = os.path.join(TEMP_RESOURCE_FOLDER, file_name)

    with open(current_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=FILE_BUFFER_SIZE):
            if chunk:
                f.write(chunk)
    return os.path.abspath(current_path)


def remove_resource_after_reading(doc_path: str):
    if os.path.exists(doc_path):
        try:
            os.remove(doc_path)
            return True
        except OSError as e:
            print(f"Error removing file {doc_path}: {e}")
    return False


def process_document(doc, committee_name, date, knesset, tries=0, force_refresh=False):
    doc["CommitteeName"] = committee_name
    doc["SessionDate"] = date
    doc_path = ""
    try:
        out_path = extract_json_path(doc, output_dir=OUTPUT_FOLDER)
        if force_refresh or not os.path.exists(out_path):
            doc_path = read_resource_from_remote(doc["FilePath"])
            text = read_doc_as_txt(doc_path)
            save_doc_as_json(text, doc, knesset, out_path)
    except Exception as e:
        print("")
        if tries < MAX_CAST_TRIES_FOR_DOC:
            print(f"Error processing {doc['FilePath']}, Trying Again. {e}")
            process_document(doc, committee_name, date,
                             knesset, tries+1, force_refresh)
        else:
            print(f"Error processing {doc['FilePath']} OUT OF TRIES")
            # Log error to a file
            error_log_file = "processing_errors.log"
            with open(error_log_file, "a", encoding="utf-8") as log_file:
                file_name = os.path.basename(
                    doc['FilePath']) if 'FilePath' in doc else "unknown"
                error_message = f"{file_name}, Error after {tries} tries: {str(e)}\n"
                log_file.write(error_message)
            print(f"Error logged to {error_log_file}")
    finally:
        remove_resource_after_reading(doc_path)


def fetch_MKs_data(knesset: int):
    uri_for_person_id = f"""https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_PersonToPosition?
    $filter=KnessetNum%20eq%20{knesset}%20
    and%20FactionName%20ne%20null&$expand=KNS_Person"""
    res = requests.get(uri_for_person_id)
    mks_list = res.json()['value']
    for mk in mks_list:
        MKS[mk["PersonID"]] = {
            "Id": mk["KNS_Person"]["Id"],
            "FirstName": mk["KNS_Person"]["FirstName"],
            "LastName": mk["KNS_Person"]["LastName"],
            "FactionName": mk["FactionName"],
            "FactionID": mk["FactionID"],
        }

    # Save MKs data to a JSON file for reference
    save_mks_to_file(MKS)
    return MKS


def save_mks_to_file(mks_data, file_path="mks_data.json"):
    """
    Save the MKs data to a JSON file for reference by other modules.

    Args:
        mks_data (dict): Dictionary containing MKs data
        file_path (str): Path where the JSON file will be saved
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mks_data, f, ensure_ascii=False, indent=2)
    print(f"MKs data saved to {file_path}")


def fetch_all_committees_from_knesset(knesset: int, force_refresh: bool):
    # TODO: figure out threads here
    # Add debug parameter with default False
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    page_size = 50
    skip = 0

    while True:
        print(
            f"Fetching committee sessions from Knesset {knesset}: skip={skip}, limit={page_size}")

        is_end = fetch_paginated_committees_from_knesset(
            knesset, page_size, skip, force_refresh)

        if not is_end or debug:
            break

        skip += page_size

    if debug:
        print("Debug mode: Only fetched first page")


def build_committees_uri(knesset: int, top: int, skip: int):
    expand_part = "$expand=KNS_CmtSessionItem%2CKNS_DocumentCommitteeSession"
    filter_part = f"$filter=KnessetNum%20eq%20{knesset}"
    pagination_part = f"$top={top}&$skip={skip}&$orderby=ID"
    return f"https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_CommitteeSession?{filter_part}&{expand_part}&{pagination_part}"


def fetch_paginated_committees_from_knesset(knesset: int, top: int, skip: int, force_refresh: bool) -> bool:
    uri = build_committees_uri(knesset, top, skip)
    response = requests.get(uri)
    committees_data = response.json()['value']
    if len(committees_data) == 0:
        return False
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for session in committees_data:
            committee_name = COMMITTEES[session["CommitteeID"]].get(
                "Name", "unknown_committee")
            date = session.get("StartDate", None)

            if COMMITTEE_SESSION_STR in session:
                for doc in session[COMMITTEE_SESSION_STR]:
                    if doc['ApplicationDesc'] == 'DOC' and doc["GroupTypeID"] == 23:
                        futures.append(executor.submit(
                            process_document, doc, committee_name, date, knesset, force_refresh))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Thread raised exception: {e}")
    return True


def init():
    global SAVE_TXT
    get_committees_data()
    os.makedirs(TEMP_RESOURCE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    parser = argparse.ArgumentParser(description="Knesset NLP")
    parser.add_argument("--save-txt", action="store_true",
                        help="Save TXT files during processing")
    args = parser.parse_args()

    SAVE_TXT = args.save_txt or os.getenv(
        'SAVE_TXT', 'false').lower() == 'true'
    return args


def process_knesset_data(knesset: int, force_refresh=False):
    init()
    fetch_MKs_data(knesset)
    fetch_all_committees_from_knesset(knesset, force_refresh)


if __name__ == "__main__":
    args = init()
    process_knesset_data(25)
