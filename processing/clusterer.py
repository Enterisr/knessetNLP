from sklearn.cluster import KMeans

from utils.logger_config import get_logger
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
import pickle
import plotly.express as px
from typing import Tuple, Optional, Dict
import os
from collections import Counter
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer


class Clusterer:
    def __init__(self,
                 embeddings_file: str = 'utterance_embeddings.npy',
                 data_file: str = 'utterances_data.pkl',
                 output_dir: str = 'clustering_results') -> None:
        self.logger = get_logger(__name__)
        self.embeddings_file = embeddings_file
        self.data_file = data_file
        self.output_dir = output_dir
        self.embeddings = None
        self.data = None
        self.cluster_labels = None
        self.reduced_embeddings = None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def load_data(self) -> Tuple[np.ndarray, pd.DataFrame]:
        self.logger.info(f"Loading embeddings from {self.embeddings_file}")
        self.embeddings = np.load(self.embeddings_file)

        self.logger.info(f"Loading utterance data from {self.data_file}")
        self.data = pickle.load(open(self.data_file, 'rb'))

        return self.embeddings, self.data

    def cluster_npy_file(self,
                         clusters_num=30,
                         sample_size: Optional[int] = None) -> np.ndarray:
        if self.embeddings is None:
            self.load_data()
        assert self.embeddings is not None

        embeddings = self.reduced_embeddings

        if sample_size and sample_size < len(embeddings):
            self.logger.info(
                f"Using sample of {sample_size} embeddings for clustering")
            indices = np.random.choice(
                len(embeddings), sample_size, replace=False)
            embeddings_to_cluster = embeddings[indices]
        else:
            self.logger.info(
                f"Using all {len(embeddings)} embeddings for clustering")
            embeddings_to_cluster = embeddings
            indices = np.arange(len(embeddings))

        self.logger.info(
            f"Clustering with kmeans with {clusters_num} clusters")

        clusterer = KMeans(n_clusters=clusters_num)
        labels = clusterer.fit_predict(embeddings_to_cluster)

        if sample_size and sample_size < len(embeddings):
            full_labels = np.full(len(embeddings), -1)
            full_labels[indices] = labels
            self.cluster_labels = full_labels
        else:
            self.cluster_labels = labels
        cluster_counts = Counter(self.cluster_labels)
        self.logger.info(f"Found {len(cluster_counts)} clusters")
        self.logger.info(
            f"Largest cluster: {max(cluster_counts.values())} utterances")
        self.logger.info(
            f"Number of noise points: {cluster_counts.get(-1, 0)}")

        # Ensure the DataFrame is defined before sampling utterances
        df = pd.DataFrame({
            'x': embeddings[:, 0],
            'y': embeddings[:, 1],
            'cluster': labels,
            'text': self.data['text'].tolist(),
            'mk': self.data['mk'].tolist()
        })

        # Print a sample of 10 utterances for each cluster
        for cluster_id in df['cluster'].unique():
            cluster_sample = df[df['cluster'] == cluster_id].sample(
                n=min(10, len(df[df['cluster'] == cluster_id])))
            self.logger.info(f"Cluster {cluster_id} sample:")
            for _, row in cluster_sample.iterrows():
                self.logger.info(f"- {row['text'][::-1]}")

        # Create a bar chart to visualize a sample of utterances for each cluster
        cluster_samples = []
        for cluster_id in df['cluster'].unique():
            cluster_sample = df[df['cluster'] == cluster_id].sample(
                n=min(10, len(df[df['cluster'] == cluster_id])))
            for _, row in cluster_sample.iterrows():
                cluster_samples.append(
                    {'Cluster': cluster_id, 'Utterance': row['text']})

        sample_df = pd.DataFrame(cluster_samples)

        fig = px.bar(
            sample_df,
            x='Cluster',
            y=sample_df.index,
            text='Utterance',
            title='Sample Utterances per Cluster',
            labels={'Cluster': 'Cluster ID', 'index': 'Sample Index'},
            color='Cluster',
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        output_path = os.path.join(
            self.output_dir, 'cluster_sample_visualization.html')
        fig.write_html(output_path)
        self.logger.info(f"Sample visualization saved to {output_path}")

        return self.cluster_labels

    def reduce_dimensions(self,
                          n_components: int = 2,
                          sample_size: Optional[int] = None) -> np.ndarray:

        if self.embeddings is None:
            self.load_data()
        assert self.embeddings is not None

        embeddings = self.embeddings

        if sample_size and sample_size < len(embeddings):
            self.logger.info(
                f"Using sample of {sample_size} embeddings for dimension reduction")
            indices = np.random.choice(
                len(embeddings), sample_size, replace=False)
            embeddings_to_reduce = embeddings[indices]
        else:
            self.logger.info(
                f"Using all {len(embeddings)} embeddings for dimension reduction")
            embeddings_to_reduce = embeddings
            indices = np.arange(len(embeddings))

        self.logger.info(
            f"Reducing dimensions with PCA (n_components={n_components})")
        reducer = PCA(n_components=n_components)
        reduced = reducer.fit_transform(embeddings_to_reduce)

        if sample_size and sample_size < len(embeddings):
            self.reduced_sample = reduced
            self.sample_indices = indices
            return reduced
        else:
            self.reduced_embeddings = reduced
            return reduced

    def generate_cluster_titles(self, top_n_words: int = 5, max_clusters: int = 20) -> Dict[int, str]:
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return {}

        if self.data is None:
            self.load_data()
        assert self.data is not None

        unique_clusters = sorted(
            [c for c in set(self.cluster_labels) if c != -1])

        if len(unique_clusters) > max_clusters:
            cluster_sizes = Counter(self.cluster_labels)
            unique_clusters = sorted(unique_clusters,
                                     key=lambda c: cluster_sizes.get(c, 0),
                                     reverse=True)[:max_clusters]

        hebrew_stopwords = set([
            'של', 'את', 'זה', 'עם', 'על', 'אני', 'הוא', 'היא', 'הם', 'אנחנו', 'אתם', 'אתן',
            'שלי', 'שלך', 'שלו', 'שלה', 'שלנו', 'שלכם', 'שלכן', 'שלהם', 'שלהן',
            'לי', 'לך', 'לו', 'לה', 'לנו', 'לכם', 'לכן', 'להם', 'להן',
            'אותי', 'אותך', 'אותו', 'אותה', 'אותנו', 'אתכם', 'אתכן', 'אותם', 'אותן',
            'וגם', 'אבל', 'או', 'אז', 'אם', 'גם', 'רק', 'כי', 'בגלל',
            'ב', 'ל', 'מ', 'י', 'כ', 'ו', 'ה',
            'כל', 'כן', 'לא', 'כמו', 'אך', 'אז', 'אבל', 'רק', 'גם',
            'sub', 'comm', 'הצעת', 'חוק', 'ועדת'
        ])

        def preprocess_text(text):
            text = text.replace('[sub:', '').replace('comm:', '')
            return text

        all_texts = [preprocess_text(text)
                     for text in self.data['text'].tolist()]

        cluster_titles = {}

        for cluster_id in tqdm(unique_clusters, desc="Generating cluster titles"):
            mask = self.cluster_labels == cluster_id
            cluster_texts_raw = self.data.iloc[mask]['text'].tolist()

            if len(cluster_texts_raw) == 0:
                cluster_titles[cluster_id] = f"Cluster {cluster_id} (empty)"
                continue

            cluster_texts = [preprocess_text(text)
                             for text in cluster_texts_raw]

            vectorizer = TfidfVectorizer(max_features=200,
                                         stop_words=list(hebrew_stopwords),
                                         ngram_range=(1, 2))
            try:
                vectorizer.fit(all_texts)
                cluster_tfidf = vectorizer.transform(cluster_texts)

                word_importance = np.array(cluster_tfidf.sum(axis=0)).flatten()
                feature_names = vectorizer.get_feature_names_out()

                top_indices = word_importance.argsort()[-top_n_words:][::-1]
                top_words = [str(feature_names[i]) for i in top_indices]

                title = f"Cluster {cluster_id}: {', '.join(top_words)}"
                cluster_titles[cluster_id] = title
            except Exception as e:
                self.logger.error(
                    f"Error generating title for cluster {cluster_id}: {e}")
                cluster_titles[cluster_id] = f"Cluster {cluster_id}"

        return cluster_titles

    def visualize_clusters_2d(self,
                              cluster_titles: Optional[Dict[int, str]] = None,
                              sample_size: int = 10000,
                              output_file: str = 'cluster_visualization.html') -> None:
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return

        if self.data is None:
            self.load_data()
        assert self.data is not None

        if self.reduced_embeddings is None and not hasattr(self, 'reduced_sample'):
            self.reduce_dimensions(n_components=2, sample_size=sample_size)

        if sample_size and sample_size < len(self.cluster_labels):
            if hasattr(self, 'sample_indices'):
                indices = self.sample_indices
            else:
                indices = np.random.choice(
                    len(self.cluster_labels), sample_size, replace=False)

            labels = self.cluster_labels[indices]
            if hasattr(self, 'reduced_sample'):
                points = self.reduced_sample
            else:
                points = self.reduce_dimensions(2, sample_size=sample_size)
            texts = self.data.iloc[indices]['text'].tolist()
            mks = self.data.iloc[indices]['mk'].tolist()
        else:
            if self.reduced_embeddings is None:
                self.reduced_embeddings = self.reduce_dimensions(2)
            points = self.reduced_embeddings
            labels = self.cluster_labels
            texts = self.data['text'].tolist()
            mks = self.data['mk'].tolist()

        df = pd.DataFrame({
            'x': points[:, 0],
            'y': points[:, 1],
            'cluster': labels,
            'text': texts,
            'mk': mks
        })

        # if cluster_titles is None:
        #     cluster_titles = self.generate_cluster_titles()

        df['hover_text'] = df.apply(
            lambda row: f"Cluster: {row['cluster']}<br>MK: {row['mk']}<br>Text: {row['text'][:100]}...",
            axis=1
        )

        fig = px.histogram(
            df,
            x='cluster',
            color='cluster',
            title='Cluster Distribution',
            labels={'cluster': 'Cluster ID', 'count': 'Number of Points'},
            nbins=len(df['cluster'].unique()),
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        output_path = os.path.join(self.output_dir, output_file)
        fig.write_html(output_path)
        self.logger.info(f"Visualization saved to {output_path}")

    def save_cluster_data(self, output_file: str = 'cluster_data.csv') -> None:
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return

        if self.data is None:
            self.load_data()
        assert self.data is not None

        result_df = self.data.copy()
        result_df['cluster'] = self.cluster_labels

        output_path = os.path.join(self.output_dir, output_file)
        result_df.to_csv(output_path, index=False)
        self.logger.info(f"Cluster data saved to {output_path}")

    def analyze_clusters_by_mk(self) -> pd.DataFrame:
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return pd.DataFrame()

        if self.data is None:
            self.load_data()
        assert self.data is not None

        df = pd.DataFrame({
            'cluster': self.cluster_labels,
            'mk': self.data['mk'].tolist(),
        })

        cluster_mk_counts = df.groupby(
            ['cluster', 'mk']).size().reset_index(name='count')

        cluster_mk_counts = cluster_mk_counts.sort_values(
            ['cluster', 'count'], ascending=[True, False])

        output_path = os.path.join(
            self.output_dir, 'cluster_mk_distribution.csv')
        cluster_mk_counts.to_csv(output_path, index=False)
        self.logger.info(f"MK distribution saved to {output_path}")

        return cluster_mk_counts
