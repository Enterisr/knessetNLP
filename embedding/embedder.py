from embedding.embed_utils import get_utterances_files_list

from sentence_transformers import SentenceTransformer

import pandas as pd
import numpy as np
import json

import gc
from pathlib import Path
from embedding.metadata_handler import embed_metadata_in_utterance
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

model = SentenceTransformer(
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
)
logger = get_logger(__name__)


class Embedder:
    """Text embedding functionality using SentenceTransformers."""

    def __init__(self):
        self.model = model


def _process_utterance_file(file_name: str, filepath: str, mk_utternces: dict, utterances: list, mk_for_df: list):
    with open(filepath, "r", encoding="utf-8") as file_content:
        file_data = json.loads(file_content.read())

        for speaker_key, values in file_data["utterances"].items():
            if mk_utternces.get(speaker_key) is None:
                mk_utternces[speaker_key] = {
                    "utterances": [], "metadata": values["metadata"], "sentiment": {}}

            mk_utternces[speaker_key]["utterances"] += values["utterances"]

            committee_prefixed_utterances = embed_metadata_in_utterance(
                values["utterances"], file_data)

            utterances += committee_prefixed_utterances

            if values.get("sentiment") is not None:
                for prop_key, prop_val in values["sentiment"].items():
                    if mk_utternces[speaker_key]["sentiment"].get(prop_key) is None:
                        mk_utternces[speaker_key]["sentiment"][prop_key] = 0

                    mk_utternces[speaker_key]["sentiment"][prop_key] += prop_val

            for i, u in enumerate(values["utterances"]):
                mk_for_df.append(
                    {'text': u, "mk": speaker_key, "src": file_name, "utter_id": f"{file_name}_{speaker_key}_{i}"})


def _load_utternaces_from_files(directory: str) -> list:
    utterances = []
    mk_utternces = {}
    mk_for_df = []

    files_to_prorcess = get_utterances_files_list(directory)
    for file_name, filepath in files_to_prorcess:
        _process_utterance_file(file_name, filepath,
                                mk_utternces, utterances, mk_for_df)

    df = pd.DataFrame(mk_for_df)
    df.to_pickle(PROJECT_ROOT / "utterances_data.pkl")
    with open(PROJECT_ROOT / "mk_utterances.jsonl", "w", encoding="utf-8") as f:
        for speaker_key, data in mk_utternces.items():
            entry = {"speaker_key": speaker_key, **data}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return utterances


def _embed_in_vector_space(utternces: list, batch_size: int = 1000) -> np.ndarray:
    """
    Embed utterances in batches to reduce memory usage.
    """
    print(f"Encoding {len(utternces)} utterances in batches...")

    all_embeddings = []
    total_batches = (len(utternces) + batch_size - 1) // batch_size

    for i in range(0, len(utternces), batch_size):
        batch_end = min(i + batch_size, len(utternces))
        batch_utterances = utternces[i:batch_end]

        print(
            f"Processing batch {i//batch_size + 1}/{total_batches} ({len(batch_utterances)} utterances)...")

        batch_embeddings = model.encode(batch_utterances,
                                        # we want to use cosine sim in FAISS, not L2, to be faster.
                                        # we also dont care about the norm, as its prone to be large as the utterance grows in length,
                                        # but we dont care about that too.
                                        normalize_embeddings=True,
                                        show_progress_bar=True,
                                        batch_size=64,
                                        convert_to_numpy=True,)

        all_embeddings.append(batch_embeddings.astype(np.float32))

        # Clear batch from memory
        del batch_embeddings, batch_utterances
        gc.collect()  # Force garbage collection

    print("Concatenating all embeddings...")
    embeddings_array = np.vstack(all_embeddings)

    # Clear the list to free memory
    del all_embeddings
    gc.collect()

    print("Encoding completed!")
    np.save(PROJECT_ROOT / "embeddings.npy", embeddings_array)

    return embeddings_array


def load_embeddings(directory: str, force_refresh=False, batch_size=1000):
    if force_refresh:
        utternaces = _load_utternaces_from_files(directory)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
        return utternaces, embeddings

    try:
        embeddings = np.load(PROJECT_ROOT / "embeddings.npy")
        df = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")
        utternaces = df["text"].tolist()
        print(f"Loaded {len(embeddings)} embeddings from file.")
    except FileNotFoundError:
        print("Embeddings file not found. Generating new embeddings...")
        utternaces = _load_utternaces_from_files(directory)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
    return utternaces, embeddings


def embed(directory="./utterances", force_refresh=False, batch_size=1000):
    utternaces, embeddings = load_embeddings(
        directory, force_refresh, batch_size)
    print("done loading!")
    return utternaces, embeddings
