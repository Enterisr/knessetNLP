import requests
import os
import json
from urllib.parse import urlparse
import re
import requests_cache
from subprocess import run
from pathlib import Path

CACHE_FILE = "knesset_cache.sqlite"
TEMP_RESOURCE_FOLDER = "temp"
OUTPUT_FOLDER = "committee_data"
FILE_BUFFER_SIZE = 8192
COMMITTEE_SESSION_STR = "KNS_DocumentCommitteeSession"
COMMITTEE_URI = "https://knesset.gov.il/OdataV4/ParliamentInfo/?committee_id$filter=KnessetNum%20eq%20{knesset}"
requests_cache.install_cache(CACHE_FILE, backend='sqlite', expire_after=3600)

COMMITTEES = {}


def read_doc_as_txt(doc: str):
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
        return f.read()


def save_doc_as_json(text: str, meta: dict, knesset_num: int, output_dir: str):
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

    output_path = os.path.join(output_dir, f"{doc_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_committees_data():
    response = requests.get(
        "https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_Committee?committee_id")
    committees_list = response.json()['value']
    for c in committees_list:
        COMMITTEES[c["Id"]] = c
    return COMMITTEES


def fetch_all_committees_from_knesset(knesset: int):
    url = f"https://knesset.gov.il/OdataV4/ParliamentInfo/KNS_CommitteeSession?$filter=KnessetNum%20eq%20{knesset}&$expand=KNS_CmtSessionItem%2CKNS_DocumentCommitteeSession"
    response = requests.get(url)
    committees_data = response.json()['value']

    for session in committees_data:
        committee_name = COMMITTEES[session["CommitteeID"]].get(
            "Name", "unknown_committee")
        date = session.get("StartDate", None)

        if COMMITTEE_SESSION_STR in session:
            for doc in session[COMMITTEE_SESSION_STR]:
                if doc['ApplicationDesc'] == 'DOC':
                    doc["CommitteeName"] = committee_name
                    doc["SessionDate"] = date
                    doc_path = ""
                    try:
                        doc_path = read_resource_from_remote(doc["FilePath"])
                        text = read_doc_as_txt(doc_path)
                        save_doc_as_json(text, doc, knesset, OUTPUT_FOLDER)
                    except Exception as e:
                        print(f"Error processing {doc['FilePath']}: {e}")
                    finally:
                        remove_resource_after_reading(doc_path)


def read_resource_from_remote(uri: str):
    cleaned_url = re.sub(r'(?<!:)//', '/', uri)
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


def init():
    get_committees_data()
    os.makedirs(TEMP_RESOURCE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# Run the pipeline
init()
fetch_all_committees_from_knesset(22)
