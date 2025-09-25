import argparse
import os
from processing.clusterer import Clusterer
from trash_utterances_detector import trainer


def main():
    """
    Main function to run the clustering analysis pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Cluster utterance embeddings.")
    parser.add_argument('--embeddings_file', type=str, default='utterance_embeddings.npy',
                        help='Path to the utterance embeddings file (.npy)')
    parser.add_argument('--data_file', type=str, default='utterances_data.pkl',
                        help='Path to the utterance data file (.pkl)')
    parser.add_argument('--output_dir', type=str, default='clustering_results',
                        help='Directory to save clustering results')
    parser.add_argument('--sample_size', type=int, default=50000,
                        help='Number of samples to use for clustering and visualization (None for all)')
    parser.add_argument('--min_cluster_size', type=int, default=50,
                        help='Minimum cluster size for HDBSCAN')
    parser.add_argument('--min_samples', type=int, default=15,
                        help='Minimum samples for HDBSCAN')
    parser.add_argument('--filter_unimportant', action='store_true', default=True,
                        help='Filter out unimportant utterances using trained classifier')
    parser.add_argument('--no_filter', action='store_true', default=False,
                        help='Disable importance filtering')
    parser.add_argument('--classifier_path', type=str, default=None,
                        help='Path to custom classifier model (optional)')

    args = parser.parse_args()

    # Handle filtering flags
    filter_unimportant = args.filter_unimportant and not args.no_filter

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    clusterer = Clusterer(
        embeddings_file=args.embeddings_file,
        data_file=args.data_file,
        output_dir=args.output_dir,
        filter_unimportant=filter_unimportant,
        classifier_path=args.classifier_path
    )

    clusterer.load_data()

    # Reduce dimensions for clustering and visualization
    clusterer.reduce_dimensions(n_components=2, sample_size=args.sample_size)

    clusterer.cluster_npy_file(
        clusters_num=30,  # Using K-means clustering
        sample_size=args.sample_size
    )

    cluster_titles = clusterer.generate_cluster_titles(max_clusters=50)

    clusterer.visualize_clusters_2d(
        cluster_titles=cluster_titles,
        sample_size=args.sample_size,
        output_file='hdbscan_cluster_visualization.html'
    )

    clusterer.save_cluster_data(output_file='hdbscan_cluster_data.csv')

    clusterer.analyze_clusters_by_mk()

    print(
        f"Clustering analysis complete. Results saved in '{args.output_dir}'.")


if __name__ == '__main__':
    #    main()
    trainer.train_classifier_with_kfold()
