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

    query_embedding = model.encode(
        [query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    k = 100

    distances, ids = repo_data.database.search(query_embedding, k)

    utters_by_mk: dict[str, dict] = {}
    print("Search results:")
    for rank, (uid, dist) in enumerate(zip(ids[0], distances[0]), start=1):
        if uid == -1:
            continue

        utter_idx = int(uid)
        row = repo_data.df.iloc[utter_idx]

        print(
            f"Match {rank}: ID {utter_idx}, score={float(dist):.4f}, Utterance: {row['text'][:120][::-1]} mk: { row['mk'][::-1]}")

        mk_id = str(row["mk_id"])
        if mk_id not in utters_by_mk:
            utters_by_mk[mk_id] = {
                "utterances": [],
                "name": row["mk"],
                "metadata": get_mks().get(mk_id),
            }

        utters_by_mk[mk_id]["utterances"].append(
            {"text": row["text"], "src": row["src"], "score": float(dist)}
        )

    return utters_by_mk


def init_repo(force_refresh: bool):
    df, embeddings, utternaces = embed(force_refresh=force_refresh)
    database = build_faiss_from_embeddings(
        embeddings, force_refresh)
    return RepoData(database, df, utternaces)


if __name__ == "__main__":
    init_repo(force_refresh=True)
