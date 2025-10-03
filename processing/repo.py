import faiss
from faiss import IndexFlatIP
from sentence_transformers import SentenceTransformer
import numpy as np
from utils.logger_config import get_logger
from pathlib import Path
from processing.embedder import embed
from processing.repo_data import RepoData
from processing.filter_db.utterance_filter import get_or_create_filtered_data
from processing.search_utils import process_search_results, build_sorted_results
import pandas as pd
logger = get_logger(__name__)

model = SentenceTransformer(
    'imvladikon/sentence-transformers-alephbert',
)
PROJECT_ROOT = Path(__file__).parent.parent
FILTER_TRESHHOLD = 0.43


def build_faiss_from_embeddings(embeddings: np.ndarray, df, force_refresh: bool) -> IndexFlatIP:
    d = embeddings.shape[1]  # get dim from embeddings

    index_path = PROJECT_ROOT / "committie_index"
    if not force_refresh and index_path.exists():
        try:
            logger.info("Loading existing FAISS index from file...")
            index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}. Building new index...")

    logger.info("Building new FAISS index...")
    logger.info(f"Embeddings shape: {embeddings.shape}")

    con_embeddings = np.ascontiguousarray(embeddings)
    index = faiss.IndexIDMap2(faiss.IndexFlatIP(d))

    ids = df.index.to_numpy(dtype=np.int64)
    logger.info(
        f"Creating IDs array: {ids.shape}, range: {ids.min()} to {ids.max()}")

    index.add_with_ids(con_embeddings, ids)

    logger.info(f"Built FAISS index with {index.ntotal} vectors")
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
    k = 300
    distances, ids = repo_data.database.search(query_embedding, k)

    mk_utterances, mk_total_scores, mk_metadata = process_search_results(
        distances, ids, repo_data.df
    )

    return build_sorted_results(mk_utterances, mk_total_scores, mk_metadata)


def init_repo(force_refresh: bool):
    """Initialize repository with importance filtering."""
    df, embeddings, utterances = embed(
        force_refresh=force_refresh)
    logger.info(
        f"Original data - DataFrame shape: {df.shape}, Embeddings shape: {embeddings.shape}")

    filtered_embeddings, filtered_df = get_or_create_filtered_data(
        embeddings, df, FILTER_TRESHHOLD, force_refresh)

    logger.info(
        f"DataFrame index info - Type: {type(filtered_df.index)}, Range: {filtered_df.index.min()} to {filtered_df.index.max()}")

    index_path = PROJECT_ROOT / "committie_index"
    need_rebuild_index = force_refresh or not index_path.exists()
    database = build_faiss_from_embeddings(
        filtered_embeddings, filtered_df, need_rebuild_index)

    return RepoData(database, filtered_df, utterances)


if __name__ == "__main__":
    init_repo(force_refresh=True)
