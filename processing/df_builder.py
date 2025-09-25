import json
import pandas as pd
from pathlib import Path
from processing.embed_utils import get_utterances_files_list
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Constants for metadata embedding
MAX_SUBJECT_LEN = 40
MAX_COMMITIEE_LEN = 40
SEP = " | "  # clearer for the model than underscores jammed together
METADATA_FORMAT = f"נושא: %s{SEP}ועדה: %s{SEP}תוכן: %s"

logger = get_logger(__name__)


def embed_metadata_in_utterance(utter_list: list[str], file_data: dict):
    """Embed metadata (subject and committee) into utterances for better context."""
    subject = str(file_data.get("subject", "Unknown Subject"))[
        :MAX_SUBJECT_LEN]
    committee = str(file_data.get("committee", "Unknown Committee"))[
        :MAX_COMMITIEE_LEN]
    for u in utter_list:
        yield METADATA_FORMAT % (subject, committee, u)


def extract_id(metadata):
    """Extract ID from metadata with error handling."""
    try:
        id = metadata["Id"]
    except:
        id = -1

    return id


def _process_utterance_file(file_name: str, filepath: str,
                            utterances: list, utterances_df_list: list):
    """Process a single utterance file and build both embedding list and DataFrame rows."""
    with open(filepath, "r", encoding="utf-8") as f:
        file_data = json.loads(f.read())

    # Make speaker iteration stable
    speakers = list((file_data.get("utterances") or {}).items())
    speakers.sort(key=lambda kv: str(kv[0]))

    for speaker_key, values in speakers:
        ulist = list(values.get("utterances", []))
        committee_prefixed_utterances = list(
            embed_metadata_in_utterance(ulist, file_data))
        utterances.extend(committee_prefixed_utterances)

        #  build DF rows in the SAME order to keep alignment
        for i, u in enumerate(ulist):
            utter_id = f"{file_name}::{speaker_key}::{i}"
            utterances_df_list.append({
                "utter_id": utter_id,
                "text": u,
                "mk": speaker_key,
                "mk_id": extract_id(values["metadata"]),
                "src": file_data["source_file"],
                "subject": str(file_data.get("subject", ""))[:MAX_SUBJECT_LEN],
                "committee": str(file_data.get("committee", ""))[:MAX_COMMITIEE_LEN],
            })


def create_df(directory: str):
    """Load utterances from all JSON files in directory and build DataFrame."""
    utterances = []
    utterances_df_list = []

    files_to_process = get_utterances_files_list(directory)
    logger.info(f"Processing {len(files_to_process)} files from {directory}")

    for file_name, filepath in files_to_process:
        _process_utterance_file(file_name, filepath,
                                utterances, utterances_df_list)

    df = pd.DataFrame(utterances_df_list)

    # Hard alignment check: lengths must match
    assert len(df) == len(
        utterances), f"DataFrame length ({len(df)}) != utterances length ({len(utterances)})"

    df.reset_index(drop=True, inplace=True)
    df["row_id"] = df.index.astype("int64")

    df.to_pickle(PROJECT_ROOT / "utterances_data.pkl")
    logger.info(
        f"Created DataFrame with {len(df)} rows and saved to utterances_data.pkl")

    return df, utterances


def recreate_utterances_from_files(directory: str):
    """Recreate the metadata-prefixed utterances from files (used when loading existing embeddings)."""
    utterances = []
    files_to_process = get_utterances_files_list(directory)

    for file_name, filepath in files_to_process:
        with open(filepath, "r", encoding="utf-8") as f:
            file_data = json.loads(f.read())
        speakers = list((file_data.get("utterances") or {}).items())
        speakers.sort(key=lambda kv: str(kv[0]))
        for speaker_key, values in speakers:
            ulist = list(values.get("utterances", []))
            committee_prefixed_utterances = list(
                embed_metadata_in_utterance(ulist, file_data))
            utterances.extend(committee_prefixed_utterances)

    return utterances
