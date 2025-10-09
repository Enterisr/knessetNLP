from processing.df_builder import (
    create_df,
    recreate_utterances_from_df,
)

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


def load_or_create_dataframe(directory: str, force_refresh=False):
    df_path = PROJECT_ROOT / "utterances_data.pkl"

    if not force_refresh and df_path.exists():
        df = pd.read_pickle(df_path)
        # Recreate utterances directly from DF to preserve exact ordering
        utterances = recreate_utterances_from_df(df)
        logger.info(f"Loaded DataFrame with {len(df)} rows from file and reconstructed {len(utterances)} utterances from DF.")
        return df, utterances

    logger.info("Creating new DataFrame...")
    df, utterances = create_df(directory)
    return df, utterances


def load_or_create_embeddings(utterances: list, force_refresh=False, batch_size=1000):
    embeddings_path = PROJECT_ROOT / "utterance_embeddings.npy"

    if not force_refresh and embeddings_path.exists():
        embeddings = np.load(embeddings_path)
        logger.info(f"Loaded {len(embeddings)} embeddings from file.")
        return embeddings

    logger.info("Creating new embeddings...")
    embeddings = _embed_in_vector_space(utterances, batch_size)
    return embeddings


def load_embeddings(directory: str, force_refresh=False, batch_size=1000):
    """Load or create both DataFrame and embeddings. Ensures both are available even if only one exists."""
    df, utterances = load_or_create_dataframe(directory, force_refresh)
    embeddings = load_or_create_embeddings(
        utterances, force_refresh, batch_size)
    return df, embeddings, utterances


def embed(directory="./utterances", force_refresh=False, batch_size=1000):
    """Main entry point for embedding functionality."""
    df, embeddings, utterances = load_embeddings(
        directory, force_refresh, batch_size)
    return df, embeddings, utterances
