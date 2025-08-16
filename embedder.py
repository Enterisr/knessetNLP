from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.decomposition import PCA
import plotly.express as px
import pandas as pd
from sklearn.metrics.pairwise import cosine_distances, euclidean_distances
import os
import numpy as np
import json


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


def _embed_in_vector_space(utternces: list) -> np.ndarray:

    model = SentenceTransformer(
        'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
    )

    print(f"Encoding {len(utternces)} utterances...")
    embeddings = model.encode(utternces,
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
    if (force_reload):
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


def embed(dir="./utterances"):
    utternaces, embeddings = load_embeddings(dir, False)
    _graph_utterances(embeddings, utternaces)
