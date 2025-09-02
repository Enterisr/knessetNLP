import json
import faiss
from faiss import IndexFlatIP
from sentence_transformers import SentenceTransformer
import numpy as np
from utils.logger_config import get_logger
from pathlib import Path
from embedding.embedder import embed
from embedding.repo_data import RepoData

logger = get_logger(__name__)

model = SentenceTransformer(
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
)

PROJECT_ROOT = Path(__file__).parent.parent


def load_mks():
    """Load Member of Knesset data from JSON file"""

    mks_path = PROJECT_ROOT / "mks_data.json"

    try:
        with open(mks_path, 'r', encoding='utf-8') as f:
            mks_data = json.load(f)
        logger.info(f"Successfully loaded {len(mks_data)} MKs from {mks_path}")
        return mks_data
    except FileNotFoundError:
        logger.error(f"MKs data file not found at {mks_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error parsing MKs JSON data at {mks_path}")
        return {}


MKS = load_mks()

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


def search(repo_data: RepoData, query: str) -> dict[str, list]:
    query_embedding = model.encode(
        [query], normalize_embeddings=True).astype(np.float32)

    k = 400  # Number of nearest neighbors to retrieve
    # search method only takes query vectors and k as parameters, it returns distances and indices
    distances, indices = repo_data.database.search(query_embedding, k)
    utters_by_mk = {}
    print("Search results:")
    for i in range(k):
        utternace_idx = indices[0][i]
        embedding_registry = repo_data.df.iloc[utternace_idx]
        print(
            f"Match {i+1}: Index {utternace_idx}, Utterance: {embedding_registry.text[::-1]}")
        mk_id = str(int(embedding_registry["mk_id"]))
        if utters_by_mk.get(mk_id) is None:
            utters_by_mk[mk_id] = {"utterances": [
            ], "name": embedding_registry["mk"], "metadata": MKS[mk_id]}

        utters_by_mk[mk_id]["utterances"].append(
            {"text": embedding_registry["text"], "src": embedding_registry["src"]})
    return utters_by_mk


def init_repo(force_refresh: bool):
    df, embeddings = embed(force_refresh=force_refresh)
    database = build_faiss_from_embeddings(embeddings, force_refresh)
    return RepoData(database, df)


if __name__ == "__main__":
    init_repo(force_refresh=True)
