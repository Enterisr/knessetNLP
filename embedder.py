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
from logger_config import get_logger

model = SentenceTransformer(
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
)
logger = get_logger(__name__)


def _load_utternaces_to_vector_space(dir: str) -> list:
    utterances = []
    mk_utternces = {}
    mk_for_df = []
    for file in os.listdir(dir):
        filepath = os.path.join(dir, file)
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
                        {'text': u, "mk": speaker_key, "src": file, "utter_id": f"{file}_{speaker_key}_{i}"})

    df = pd.DataFrame(mk_for_df)
    df.to_pickle("utterances_data.pkl")
    with open("mk_utterances.jsonl", "w", encoding="utf-8") as f:
        for speaker_key, data in mk_utternces.items():
            entry = {"speaker_key": speaker_key, **data}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return utterances


def build_faiss_from_embeddings(embeddings: np.ndarray, force_reload: bool) -> IndexFlatIP:
    d = embeddings.shape[1]  # get dim from embeddings

    # Try to load existing index if not forcing reload
    if not force_reload and os.path.exists("committie_index"):
        try:
            logger.info("Loading existing FAISS index from file...")
            index = faiss.read_index("committie_index")
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}. Building new index...")

    # Build new index if needed
    logger.info("Building new FAISS index...")
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    faiss.write_index(index, "committie_index")
    return index


def _embed_in_vector_space(utternces: list) -> np.ndarray:

    print(f"Encoding {len(utternces)} utterances...")
    embeddings = model.encode(utternces,
                              # we want to use cosine sim in FAISS, not L2, to be faster.
                              # we also dont care about the norm, as its prone to be large as the utterance grows in length,
                              # but we dont care about that too.
                              normalize_embeddings=True,
                              show_progress_bar=True,
                              batch_size=64,
                              convert_to_numpy=True,)
    print("Encoding completed!")

    embeddings_array = embeddings.astype(np.float32)

    np.save("embeddings.npy", embeddings_array)

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


def load_embeddings(dir: str, force_reload=False):
    if force_reload:
        utternaces = _load_utternaces_to_vector_space(dir)
        embeddings = _embed_in_vector_space(utternaces)
        return utternaces, embeddings

    try:
        embeddings = np.load("embeddings.npy")
        df = pd.read_pickle("utterances_data.pkl")
        utternaces = df["text"].tolist()
        print(f"Loaded {len(embeddings)} embeddings from file.")
    except FileNotFoundError:
        print("Embeddings file not found. Generating new embeddings...")
        utternaces = _load_utternaces_to_vector_space(dir)
        embeddings = _embed_in_vector_space(utternaces)
    return utternaces, embeddings


def embed(dir="./utterances", force_refresh=False):
    utternaces, embeddings = load_embeddings(dir, force_refresh)
    print("done loading!")
    return utternaces, embeddings

#    _graph_utterances(embeddings, utternaces)


if __name__ == "__main__":
    utternaces, embeddings = embed(force_refresh=False)
    database = build_faiss_from_embeddings(embeddings)

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
