import json
import os
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from processing.embed_utils import get_utterances_files_list
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Constants for metadata embedding
MAX_SUBJECT_LEN = 150
MAX_COMMITIEE_LEN = 150
SEP = " | "
METADATA_FORMAT = f"נושא: %s{SEP}ועדה: %s{SEP}תוכן: %s"

logger = get_logger(__name__)


def make_faiss_uid(utter_id: str) -> int:
    # EXACTLY the same hashing you used in Colab
    # If Colab used a salt like "|text", add it here and there as well.
    return int(hashlib.sha1(utter_id.encode("utf-8")).hexdigest(), 16) % (2**63)


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
        return (metadata or {}).get("Id", -1)
    except Exception:
        return -1


def align_df_to_manifest(df: pd.DataFrame) -> pd.DataFrame:
    """Align DataFrame to utter_ids.npy manifest order if it exists."""
    ids_path = PROJECT_ROOT / "utter_ids.npy"
    if not ids_path.exists():
        return df

    ids = np.load(ids_path).astype("int64")
    # Make sure all ids in manifest exist in this DF; report if some are missing
    df_ids_set = set(df["faiss_uid"].tolist())
    missing = [int(x) for x in ids if x not in df_ids_set]
    if missing:
        logger.warning(
            f"{len(missing)} ids from utter_ids.npy were not found in local DF.")
    # Reindex to the manifest order, dropping missing to keep order tight
    df = (df.set_index("faiss_uid")
            .reindex(ids)
            .dropna(subset=["utter_id"])
            .reset_index())
    logger.info("Aligned DF to utter_ids.npy order.")
    return df


def _process_utterance_file(file_name: str, filepath: str,
                            utterances: list, utterances_df_list: list):
    """Process a single utterance file and build both embedding list and DataFrame rows."""
    with open(filepath, "r", encoding="utf-8") as f:
        file_data = json.loads(f.read())

    speakers = list((file_data.get("utterances") or {}).items())
    speakers.sort(key=lambda kv: str(kv[0]))  # stable by speaker key

    for speaker_key, values in speakers:
        ulist = list(values.get("utterances", []))
        committee_prefixed_utterances = list(
            embed_metadata_in_utterance(ulist, file_data))
        utterances.extend(committee_prefixed_utterances)

        for i, u in enumerate(ulist):
            # IMPORTANT: this must match the Colab convention exactly
            utter_id = f"{file_name}::{str(speaker_key)}::{i}"
            utterances_df_list.append({
                "utter_id": utter_id,
                "text": u,
                "mk": speaker_key,
                "mk_id": extract_id(values.get("metadata", {})),
                "src": file_data.get("source_file", ""),
                "subject": str(file_data.get("subject", ""))[:MAX_SUBJECT_LEN],
                "committee": str(file_data.get("committee", ""))[:MAX_COMMITIEE_LEN],
            })


def create_df(directory: str):
    """Load utterances from all JSON files in directory and build DataFrame."""
    utterances: list[str] = []
    utterances_df_list: list[dict] = []

    files_to_process = get_utterances_files_list(directory)
    # Ensure deterministic order even if the helper returns arbitrary ordering
    files_to_process = sorted(
        files_to_process,
        key=lambda t: (str(t[0]).lower(), str(t[1]).lower())
    )
    logger.info(f"Processing {len(files_to_process)} files from {directory}")

    for file_name, filepath in files_to_process:
        _process_utterance_file(file_name, filepath,
                                utterances, utterances_df_list)

    df = pd.DataFrame(utterances_df_list)

    # Hard alignment check: lengths must match
    assert len(df) == len(utterances), \
        f"DataFrame length ({len(df)}) != utterances length ({len(utterances)})"

    df["faiss_uid"] = df["utter_id"].apply(make_faiss_uid)

    assert df["utter_id"].is_unique, "utter_id collisions detected"
    assert df["faiss_uid"].is_unique, "faiss_uid collisions detected"

    # Align to colab  manifest order if it exists (if we embedded oin colab)
    df = align_df_to_manifest(df)

    # Persist with faiss_uid present (index as columns is usually safer)
    out_path = PROJECT_ROOT / "utterances_data.pkl"
    df.to_pickle(out_path)
    logger.info(
        f"Created DataFrame with {len(df)} rows and saved to {out_path}")

    return df, utterances


def recreate_utterances_from_df(df: 'pd.DataFrame') -> list[str]:  # type: ignore[name-defined]
    """Recreate metadata-prefixed utterances directly from an existing DataFrame.

    This guarantees the exact ordering matches the DataFrame rows (important
    when aligning with stored embeddings or utter_ids manifest) and avoids
    re-reading & re-sorting the raw JSON source files which may introduce
    ordering drift.
    """

    required_cols = {"subject", "committee", "text"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    utterances = [
        METADATA_FORMAT % (row.subject, row.committee, row.text)
        for row in df.itertuples(index=False)
    ]
    return utterances
