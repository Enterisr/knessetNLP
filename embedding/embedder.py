from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.decomposition import PCA
import plotly.express as px
import pandas as pd
import os
import numpy as np
import json
import faiss
from faiss import IndexFlatIP
from utils.logger_config import get_logger
import gc
from pathlib import Path

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


def _load_utternaces_to_vector_space(dir: str) -> list:
    utterances = []
    mk_utternces = {}
    mk_for_df = []

    # Check for partition folders
    items_in_dir = os.listdir(dir)
    partition_folders = [
        item for item in items_in_dir
        if item.startswith("part_") and os.path.isdir(os.path.join(dir, item))
    ]

    if not partition_folders:
        raise ValueError(
            f"No partition folders found in {dir}. Expected folders named 'part_0', 'part_1', etc.")

    files_to_process = []

    # Process files from all partition folders
    logger.info("Found %d partition folders: %s", len(
        partition_folders), sorted(partition_folders))
    for partition_folder in sorted(partition_folders):
        partition_path = os.path.join(dir, partition_folder)
        for file_name in os.listdir(partition_path):
            if file_name.endswith('.json'):
                full_path = os.path.join(partition_path, file_name)
                files_to_process.append((file_name, full_path))

    logger.info("Processing %d utterance files from %d partitions",
                len(files_to_process), len(partition_folders))

    for file_name, filepath in files_to_process:
        with open(filepath, "r", encoding="utf-8") as file_content:
            utterances_obj = json.loads(file_content.read())

            for speaker_key, values in utterances_obj["utterances"].items():
                if (mk_utternces.get(speaker_key) is None):
                    mk_utternces[speaker_key] = {
                        "utterances": [], "metadata": values["metadata"], "sentiment": {}}

                mk_utternces[speaker_key]["utterances"] += values["utterances"]
                committee_prefixed_utterances = [
                    f"{utterances_obj['committee']}: {u}" for u in values["utterances"]]
                utterances += committee_prefixed_utterances

                if values.get("sentiment") is not None:
                    for prop_key, prop_val in values["sentiment"].items():
                        if (mk_utternces[speaker_key]["sentiment"].get(prop_key) is None):
                            mk_utternces[speaker_key]["sentiment"][prop_key] = 0

                        mk_utternces[speaker_key]["sentiment"][prop_key] += prop_val

                for i, u in enumerate(values["utterances"]):
                    mk_for_df.append(
                        {'text': u, "mk": speaker_key, "src": file_name, "utter_id": f"{file_name}_{speaker_key}_{i}"})

    df = pd.DataFrame(mk_for_df)
    df.to_pickle(PROJECT_ROOT / "utterances_data.pkl")
    with open(PROJECT_ROOT / "mk_utterances.jsonl", "w", encoding="utf-8") as f:
        for speaker_key, data in mk_utternces.items():
            entry = {"speaker_key": speaker_key, **data}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return utterances


def build_faiss_from_embeddings(embeddings: np.ndarray, force_reload: bool) -> IndexFlatIP:
    d = embeddings.shape[1]  # get dim from embeddings

    # Try to load existing index if not forcing reload
    index_path = PROJECT_ROOT / "committie_index"
    if not force_reload and index_path.exists():
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


def _graph_utterances(embeddings, sentences):
    pca = PCA(n_components=3)
    indices = np.random.choice(len(embeddings), 100)
    sentences_arr = np.array(sentences)
    embeddings_3d = pca.fit_transform(embeddings[indices])
    cosine_sims = cosine_similarity(embeddings)
    df = pd.DataFrame({
        'x': embeddings_3d[:, 0],  # x coords for sentences
        'y': embeddings_3d[:, 1],
        'z': embeddings_3d[:, 2],
        'text': sentences_arr[indices]
    })

    fig = px.scatter(df,  x='x', y='y', text='text',
                     color="z", color_continuous_scale="aggrnyl")  # i dont have good area comprehnsion so this is a middle ground
    fig.update_traces(
        marker=dict(size=14),
        textposition='bottom center'
    )
    fig.show()
    fig.write_html("PCA_plotly_SBert.html")


def load_embeddings(dir: str, force_reload=False, batch_size=1000):
    if force_reload:
        utternaces = _load_utternaces_to_vector_space(dir)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
        return utternaces, embeddings

    try:
        embeddings = np.load(PROJECT_ROOT / "embeddings.npy")
        df = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")
        utternaces = df["text"].tolist()
        print(f"Loaded {len(embeddings)} embeddings from file.")
    except FileNotFoundError:
        print("Embeddings file not found. Generating new embeddings...")
        utternaces = _load_utternaces_to_vector_space(dir)
        embeddings = _embed_in_vector_space(utternaces, batch_size)
    return utternaces, embeddings


def embed(dir="./utterances", force_refresh=False, batch_size=1000):
    utternaces, embeddings = load_embeddings(dir, force_refresh, batch_size)
    print("done loading!")
    return utternaces, embeddings

#    _graph_utterances(embeddings, utternaces)


if __name__ == "__main__":
    utternaces, embeddings = embed(force_refresh=True)
    database = build_faiss_from_embeddings(embeddings, force_reload=True)

    while True:
        query = input("search for intresting sentence: ")

        query_embedding = model.encode(
            [query], normalize_embeddings=True).astype(np.float32)

        k = 100  # Number of nearest neighbors to retrieve
        # No need to pre-allocate arrays, search returns them directly
        distances, indices = database.search(query_embedding, k)

        print("Search results:")
        for i in range(k):
            utternace_idx = indices[0][i]
            print(
                f"Match {i+1}: Index {utternace_idx}, Utterance: {utternaces[utternace_idx][::-1]}")
