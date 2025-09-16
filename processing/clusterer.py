from utils.logger_config import get_logger
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Tuple, Optional, Dict, Any, Union
import os
from collections import Counter
# import umap  # Uncomment if installed
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.feature_extraction.text import TfidfVectorizer


class Clusterer:
    def __init__(self,
                 embeddings_file: str = 'utterance_embeddings.npy',
                 data_file: str = 'utterances_data.pkl',
                 output_dir: str = 'clustering_results') -> None:
        """
        Initialize the Clusterer with paths to embedding and data files.

        Args:
            embeddings_file: Path to the npy file containing embeddings
            data_file: Path to the pickle file containing utterance data
            output_dir: Directory to save clustering results
        """
        self.logger = get_logger(__name__)
        self.embeddings_file = embeddings_file
        self.data_file = data_file
        self.output_dir = output_dir
        self.embeddings = None
        self.data = None
        self.cluster_labels = None
        self.cluster_centers = None
        self.reduced_embeddings = None

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def load_data(self) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Load embeddings and utterance data.

        Returns:
            Tuple of embeddings array and utterance dataframe
        """
        self.logger.info(f"Loading embeddings from {self.embeddings_file}")
        self.embeddings = np.load(self.embeddings_file)

        self.logger.info(f"Loading utterance data from {self.data_file}")
        self.data = pickle.load(open(self.data_file, 'rb'))

        return self.embeddings, self.data

    def cluster_npy_file(self,
                         method: str = 'hdbscan',
                         n_clusters: int = 100,
                         min_cluster_size: int = 30,
                         min_samples: int = 10,
                         sample_size: Optional[int] = None) -> np.ndarray:
        """
        Cluster the embeddings using the specified method.

        Args:
            method: Clustering method ('hdbscan' or 'kmeans')
            n_clusters: Number of clusters for KMeans
            min_cluster_size: Minimum cluster size for HDBSCAN
            min_samples: Minimum samples for HDBSCAN
            sample_size: Number of samples to use (for large datasets)

        Returns:
            Array of cluster labels
        """
        if self.embeddings is None:
            self.load_data()

        embeddings = self.embeddings  # Use a local variable to avoid None type errors

        # If sample size is provided, use a subset of the data
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

        # Perform clustering
        if method.lower() == 'hdbscan':
            self.logger.info(
                f"Clustering with HDBSCAN (min_cluster_size={min_cluster_size}, min_samples={min_samples})")
            clusterer = HDBSCAN(min_cluster_size=min_cluster_size,
                                min_samples=min_samples,
                                metric='euclidean',
                                core_dist_n_jobs=-1)
            labels = clusterer.fit_predict(embeddings_to_cluster)
        elif method.lower() == 'kmeans':
            self.logger.info(
                f"Clustering with KMeans (n_clusters={n_clusters})")
            clusterer = KMeans(n_clusters=n_clusters,
                               random_state=42, n_init=10)
            labels = clusterer.fit_predict(embeddings_to_cluster)
            self.cluster_centers = clusterer.cluster_centers_
        else:
            raise ValueError(f"Unknown clustering method: {method}")

        # If we used a sample, assign full dataset to clusters
        if sample_size and sample_size < len(embeddings):
            # For KMeans, we can use the trained model to predict clusters for all data
            if method.lower() == 'kmeans':
                self.logger.info("Predicting clusters for full dataset")
                self.cluster_labels = clusterer.predict(embeddings)
            # For HDBSCAN, we'll just have labels for the sampled points
            else:
                full_labels = np.full(len(embeddings), -1)
                full_labels[indices] = labels
                self.cluster_labels = full_labels
        else:
            self.cluster_labels = labels

        # Log cluster distribution
        cluster_counts = Counter(self.cluster_labels)
        self.logger.info(f"Found {len(cluster_counts)} clusters")
        self.logger.info(
            f"Largest cluster: {max(cluster_counts.values())} utterances")
        self.logger.info(
            f"Number of noise points: {cluster_counts.get(-1, 0)}")

        return self.cluster_labels

    def reduce_dimensions(self,
                          method: str = 'pca',
                          n_components: int = 2,
                          sample_size: Optional[int] = None) -> np.ndarray:
        """
        Reduce the dimensionality of embeddings for visualization.

        Args:
            method: Dimensionality reduction method ('pca' or 'umap')
            n_components: Number of dimensions to reduce to
            sample_size: Number of samples to use (for large datasets)

        Returns:
            Array of reduced embeddings
        """
        if self.embeddings is None:
            self.load_data()

        embeddings = self.embeddings  # Use a local variable to avoid None type errors

        # If sample size is provided, use a subset of the data
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

        # Perform dimensionality reduction
        if method.lower() == 'pca':
            self.logger.info(
                f"Reducing dimensions with PCA (n_components={n_components})")
            reducer = PCA(n_components=n_components)
            reduced = reducer.fit_transform(embeddings_to_reduce)
        elif method.lower() == 'umap':
            try:
                # Try to import UMAP if available
                from umap import UMAP
                self.logger.info(
                    f"Reducing dimensions with UMAP (n_components={n_components})")
                reducer = UMAP(n_components=n_components, random_state=42)
                reduced = reducer.fit_transform(embeddings_to_reduce)
            except ImportError:
                self.logger.warning("UMAP not installed. Falling back to PCA.")
                reducer = PCA(n_components=n_components)
                reduced = reducer.fit_transform(embeddings_to_reduce)
        else:
            raise ValueError(f"Unknown dimension reduction method: {method}")

        # Store the reduced embeddings
        if sample_size and sample_size < len(embeddings):
            # We only have reduced embeddings for the sample
            self.reduced_sample = reduced
            self.sample_indices = indices
            return reduced
        else:
            self.reduced_embeddings = reduced
            return reduced

    def generate_cluster_titles(self, top_n_words: int = 5, max_clusters: int = 20) -> Dict[int, str]:
        """
        Generate titles for each cluster based on TF-IDF analysis of utterances.

        Args:
            top_n_words: Number of words to include in each title
            max_clusters: Maximum number of clusters to generate titles for

        Returns:
            Dictionary mapping cluster IDs to titles
        """
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return {}

        if self.data is None:
            self.load_data()

        # Get unique cluster labels (excluding noise points)
        unique_clusters = sorted(
            [c for c in set(self.cluster_labels) if c != -1])

        # Limit to max_clusters if needed
        if len(unique_clusters) > max_clusters:
            cluster_sizes = Counter(self.cluster_labels)
            # Sort clusters by size (largest first)
            unique_clusters = sorted(unique_clusters,
                                     key=lambda c: cluster_sizes.get(c, 0),
                                     reverse=True)[:max_clusters]

        # Define Hebrew stopwords
        hebrew_stopwords = set([
            'של', 'את', 'זה', 'עם', 'על', 'אני', 'הוא', 'היא', 'הם', 'אנחנו', 'אתם', 'אתן',
            'שלי', 'שלך', 'שלו', 'שלה', 'שלנו', 'שלכם', 'שלכן', 'שלהם', 'שלהן',
            'לי', 'לך', 'לו', 'לה', 'לנו', 'לכם', 'לכן', 'להם', 'להן',
            'אותי', 'אותך', 'אותו', 'אותה', 'אותנו', 'אתכם', 'אתכן', 'אותם', 'אותן',
            'וגם', 'אבל', 'או', 'אז', 'אם', 'גם', 'רק', 'כי', 'בגלל',
            'ב', 'ל', 'מ', 'י', 'כ', 'ו', 'ה',
            'כל', 'כן', 'לא', 'כמו', 'אך', 'אז', 'אבל', 'רק', 'גם',
            'sub', 'comm', 'הצעת', 'חוק', 'ועדת'  # Add common prefixes from the data
        ])

        # Preprocess text function to extract more meaningful terms
        def preprocess_text(text):
            # Remove common prefixes and annotations
            text = text.replace('[sub:', '').replace('comm:', '')
            # Return cleaned text
            return text

        # Create a corpus of all texts for comparison
        all_texts = [preprocess_text(text)
                     for text in self.data['text'].tolist()]

        cluster_titles = {}

        for cluster_id in tqdm(unique_clusters, desc="Generating cluster titles"):
            # Get utterances for this cluster
            mask = self.cluster_labels == cluster_id
            cluster_texts_raw = self.data.iloc[mask]['text'].tolist()

            if len(cluster_texts_raw) == 0:
                cluster_titles[cluster_id] = f"Cluster {cluster_id} (empty)"
                continue

            # Preprocess texts
            cluster_texts = [preprocess_text(text)
                             for text in cluster_texts_raw]

            # Use TF-IDF to find important words
            vectorizer = TfidfVectorizer(max_features=200,
                                         stop_words=list(hebrew_stopwords),
                                         ngram_range=(1, 2))  # Include bigrams
            try:
                # Fit on all texts but transform only cluster texts
                vectorizer.fit(all_texts)
                cluster_tfidf = vectorizer.transform(cluster_texts)

                # Sum the TF-IDF scores for each word across all documents
                word_importance = np.array(cluster_tfidf.sum(axis=0)).flatten()
                feature_names = vectorizer.get_feature_names_out()

                # Get top words
                top_indices = word_importance.argsort()[-top_n_words:][::-1]
                top_words = [str(feature_names[i]) for i in top_indices]

                # Create title
                title = f"Cluster {cluster_id}: {', '.join(top_words)}"
                cluster_titles[cluster_id] = title
            except Exception as e:
                # Fallback if TF-IDF fails
                self.logger.error(
                    f"Error generating title for cluster {cluster_id}: {e}")
                cluster_titles[cluster_id] = f"Cluster {cluster_id}"

        return cluster_titles

    def visualize_clusters_2d(self,
                              cluster_titles: Optional[Dict[int, str]] = None,
                              sample_size: int = 10000,
                              output_file: str = 'cluster_visualization.html') -> None:
        """
        Create a 2D interactive visualization of clusters.

        Args:
            cluster_titles: Dictionary mapping cluster IDs to titles
            sample_size: Number of points to sample for visualization
            output_file: Path to save the HTML visualization
        """
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return

        # Reduce dimensions for visualization if not already done
        if self.reduced_embeddings is None:
            self.reduce_dimensions(
                method='pca', n_components=2, sample_size=sample_size)

        if sample_size and sample_size < len(self.cluster_labels):
            # Sample points for visualization
            indices = np.random.choice(
                len(self.cluster_labels), sample_size, replace=False)
            labels = self.cluster_labels[indices]
            if hasattr(self, 'reduced_sample'):
                points = self.reduced_sample
            else:
                points = self.reduced_embeddings[indices]
            texts = self.data.iloc[indices]['text'].tolist()
            mks = self.data.iloc[indices]['mk'].tolist()
        else:
            points = self.reduced_embeddings
            labels = self.cluster_labels
            texts = self.data['text'].tolist()
            mks = self.data['mk'].tolist()

        # Prepare data for plotting
        df = pd.DataFrame({
            'x': points[:, 0],
            'y': points[:, 1],
            'cluster': labels,
            'text': texts,
            'mk': mks
        })

        # Generate cluster titles if not provided
        if cluster_titles is None:
            cluster_titles = self.generate_cluster_titles()

        # Create hover text
        df['hover_text'] = df.apply(
            lambda row: f"Cluster: {row['cluster']}<br>MK: {row['mk']}<br>Text: {row['text'][:100]}...",
            axis=1
        )

        # Create figure
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='cluster',
            hover_data=['hover_text'],
            title='Utterance Clusters',
            color_continuous_scale=px.colors.qualitative.Bold,
            labels={'x': 'Dimension 1', 'y': 'Dimension 2'},
            size_max=10
        )

        # Add cluster labels if we have them
        if self.cluster_centers is not None and hasattr(self, 'reduced_embeddings'):
            # We need to reduce the cluster centers to 2D as well
            pca = PCA(n_components=2)
            centers_2d = pca.fit_transform(self.cluster_centers)

            # Add text annotations for each cluster center
            for i, (x, y) in enumerate(centers_2d):
                if i in cluster_titles:
                    title = cluster_titles[i]
                else:
                    title = f"Cluster {i}"

                fig.add_annotation(
                    x=x,
                    y=y,
                    text=title,
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40
                )

        # Save and show figure
        output_path = os.path.join(self.output_dir, output_file)
        fig.write_html(output_path)
        self.logger.info(f"Visualization saved to {output_path}")

        return fig

    def save_cluster_data(self, output_file: str = 'cluster_data.csv') -> None:
        """
        Save clustering results to a CSV file.

        Args:
            output_file: Path to save the CSV file
        """
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return

        if self.data is None:
            self.load_data()

        # Create a copy of the dataframe with cluster labels
        result_df = self.data.copy()
        result_df['cluster'] = self.cluster_labels

        # Save to CSV
        output_path = os.path.join(self.output_dir, output_file)
        result_df.to_csv(output_path, index=False)
        self.logger.info(f"Cluster data saved to {output_path}")

    def analyze_clusters_by_mk(self) -> pd.DataFrame:
        """
        Analyze the distribution of MKs across clusters.

        Returns:
            DataFrame with analysis results
        """
        if self.cluster_labels is None:
            self.logger.error("No clusters found. Run cluster_npy_file first.")
            return pd.DataFrame()

        if self.data is None:
            self.load_data()

        # Create a dataframe with cluster and MK information
        df = pd.DataFrame({
            'cluster': self.cluster_labels,
            'mk': self.data['mk'].tolist(),
            'mk_id': self.data['mk_id'].tolist()
        })

        # Count MKs in each cluster
        cluster_mk_counts = df.groupby(
            ['cluster', 'mk']).size().reset_index(name='count')

        # Sort by cluster and count
        cluster_mk_counts = cluster_mk_counts.sort_values(
            ['cluster', 'count'], ascending=[True, False])

        # Save to CSV
        output_path = os.path.join(
            self.output_dir, 'cluster_mk_distribution.csv')
        cluster_mk_counts.to_csv(output_path, index=False)
        self.logger.info(f"MK distribution saved to {output_path}")

        return cluster_mk_counts
