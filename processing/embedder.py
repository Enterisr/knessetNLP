from processing.embed_utils import get_utterances_files_list
from processing.df_builder import create_df, recreate_utterances_from_files

from sentence_transformers import SentenceTransformer

import pandas as pd
import numpy as np

import gc
from pathlib import Path
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

model = SentenceTransformer(
    'imvladikon/sentence-transformers-alephbert',
)
logger = get_logger(__name__)


class Embedder:
    """Text embedding functionality using SentenceTransformers."""

    def __init__(self):
        self.model = model


def _embed_in_vector_space(utternces: list, batch_size: int = 1000) -> np.ndarray:
    """
    Embed utterances in batches to reduce memory usage.
    """
    logger.info(f"Encoding {len(utternces)} utterances in batches...")

    all_embeddings = []
    total_batches = (len(utternces) + batch_size - 1) // batch_size

    for i in range(0, len(utternces), batch_size):
        batch_end = min(i + batch_size, len(utternces))
        batch_utterances = utternces[i:batch_end]

        logger.info(
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

    logger.info("Concatenating all embeddings...")
    embeddings_array = np.vstack(all_embeddings)

    # Clear the list to free memory
    del all_embeddings
    gc.collect()

    logger.info("Encoding completed!")
    np.save(PROJECT_ROOT / "utterance_embeddings.npy", embeddings_array)

    return embeddings_array


def load_embeddings(directory: str, force_refresh=False, batch_size=1000):
    if force_refresh:
        df, utternaces = create_df(directory)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
        return df, embeddings, utternaces

    try:
        embeddings = np.load(PROJECT_ROOT / "utterance_embeddings.npy")
        df = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")
        # The utterances in the embedding are the metadata-prefixed versions
        # We need to recreate them from the files
        utternaces = recreate_utterances_from_files(directory)

        logger.info(f"Loaded {len(embeddings)} embeddings from file.")
    except FileNotFoundError:
        logger.warning(
            "Embeddings file not found. Generating new embeddings...")
        df, utternaces = create_df(directory)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
    return df, embeddings, utternaces


def embed(directory="./utterances", force_refresh=False, batch_size=1000):
    df, embeddings, utternaces = load_embeddings(
        directory, force_refresh, batch_size)
    return df, embeddings, utternaces
