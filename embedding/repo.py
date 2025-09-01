
import faiss
from faiss import IndexFlatIP
from sentence_transformers import SentenceTransformer
import numpy as np
from utils.logger_config import get_logger
from pathlib import Path
from embedder import embed
from repo_data import RepoData

logger = get_logger(__name__)

model = SentenceTransformer(
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
)

PROJECT_ROOT = Path(__file__).parent.parent


def build_faiss_from_embeddings(embeddings: np.ndarray, force_refresh: bool) -> IndexFlatIP:
    d = embeddings.shape[1]  # get dim from embeddings

    # Try to load existing index if not forcing reload
    index_path = PROJECT_ROOT / "committie_index"
    if not force_refresh and index_path.exists():
        try:
            logger.info("Loading existing FAISS index from file...")
            index = faiss.read_index(str(index_path))
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}. Building new index...")

    # Build new index if needed
    logger.info("Building new FAISS index...")
    index = faiss.IndexFlatIP(d)

    index.add(embeddings)
    faiss.write_index(index, str(index_path))
    return index


def search(repo_data: RepoData, query: str) -> None:
    query_embedding = model.encode(
        [query], normalize_embeddings=True).astype(np.float32)

    k = 100  # Number of nearest neighbors to retrieve
    # search method only takes query vectors and k as parameters, it returns distances and indices
    distances, indices = repo_data.database.search(query_embedding, k)

    print("Search results:")
    for i in range(k):
        utternace_idx = indices[0][i]
        print(
            f"Match {i+1}: Index {utternace_idx}, Utterance: {repo_data.utternaces[utternace_idx][::-1]}")


def init_repo(force_refresh: bool):
    utternaces, embeddings = embed(force_refresh=force_refresh)
    database = build_faiss_from_embeddings(embeddings, force_refresh)
    return RepoData(database, utternaces)


if __name__ == "__main__":
    init_repo(force_refresh=True)
