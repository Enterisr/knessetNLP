import json
import faiss
from faiss import IndexFlatIP
from sentence_transformers import SentenceTransformer
import numpy as np
from utils.logger_config import get_logger
from pathlib import Path
from processing.embedder import embed
from processing.repo_data import RepoData
from processing.mk_database import get_mks
from processing.filter_db.utterance_filter import filter_and_save_utterances
from processing.search_utils import process_search_results, build_sorted_results
import pandas as pd

logger = get_logger(__name__)

model = SentenceTransformer(
    'imvladikon/sentence-transformers-alephbert',
)
PROJECT_ROOT = Path(__file__).parent.parent


def build_faiss_from_embeddings(embeddings: np.ndarray, force_refresh: bool) -> IndexFlatIP:
    d = embeddings.shape[1]  # get dim from embeddings

    index_path = PROJECT_ROOT / "committie_index"
    if not force_refresh and index_path.exists():
        try:
            logger.info("Loading existing FAISS index from file...")
            index = faiss.read_index(str(index_path))
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}. Building new index...")

    logger.info("Building new FAISS index...")
    con_embeddings = np.ascontiguousarray(embeddings)
    index = faiss.IndexIDMap2(faiss.IndexFlatIP(d))
    ids = np.arange(embeddings.shape[0], dtype=np.int64)
    index.add_with_ids(np.ascontiguousarray(
        con_embeddings, dtype=np.float32), ids)

    faiss.write_index(index, str(index_path))
    return index


def search(repo_data: RepoData, query: str) -> dict[str, dict]:
    """
    Search for utterances matching the query and return results grouped by MK.

    Args:
        repo_data: Repository data containing FAISS database and dataframe
        query: Search query string

    Returns:
        Dictionary of MK results sorted by total relevance score
    """
    query_embedding = model.encode(
        [query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    k = 200
    distances, ids = repo_data.database.search(query_embedding, k)

    mk_utterances, mk_total_scores, mk_metadata = process_search_results(
        distances, ids, repo_data.df
    )

    return build_sorted_results(mk_utterances, mk_total_scores, mk_metadata)


def init_repo(force_refresh: bool):
    """Initialize repository with importance filtering."""
    df, embeddings, utterances = embed(force_refresh=force_refresh)

    # Check if filtered files exist
    filtered_embeddings_path = PROJECT_ROOT / "filtered_utterance_embeddings.npy"
    filtered_df_path = PROJECT_ROOT / "filtered_utterances_data.pkl"

    need_filter = (force_refresh or
                   not filtered_embeddings_path.exists() or
                   not filtered_df_path.exists())

    if need_filter:
        logger.info("Creating filtered data...")
        filtered_embeddings, filtered_df = filter_and_save_utterances(
            embeddings, df, 0.43)
    else:
        logger.info("Loading existing filtered data...")
        filtered_embeddings = np.load(filtered_embeddings_path)
        filtered_df = pd.read_pickle(filtered_df_path)

    # Build or load FAISS index
    index_path = PROJECT_ROOT / "committie_index"
    need_rebuild_index = force_refresh or not index_path.exists()
    database = build_faiss_from_embeddings(
        filtered_embeddings, need_rebuild_index)

    return RepoData(database, filtered_df, utterances)


if __name__ == "__main__":
    init_repo(force_refresh=True)
