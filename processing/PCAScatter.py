

from sklearn.decomposition import PCA
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd


def graph_utterances(embeddings, sentences):
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
