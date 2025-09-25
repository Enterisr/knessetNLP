"""
Test script to verify the importance filtering integration works correctly.
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from trash_utterances_detector.predictor import UtteranceImportancePredictor
from utils.logger_config import get_logger

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent


def test_predictor():
    """Test the importance predictor on a sample of data."""
    logger.info("Testing importance predictor...")
    # Load sample data
    # Sample random 1000 utterances
    all_embeddings = np.load(PROJECT_ROOT / "utterance_embeddings.npy")
    all_data = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")

    # Generate random indices
    total_samples = len(all_embeddings)
    random_indices = np.random.choice(total_samples, size=1000, replace=False)

    # Select random samples
    embeddings = all_embeddings[random_indices]
    data = all_data.iloc[random_indices]

    logger.info(f"Testing with {len(embeddings)} utterances")

    # Initialize predictor
    predictor = UtteranceImportancePredictor()

    # Test filtering
    filtered_embeddings, filtered_data, importance_scores, important_indices = predictor.filter_important_utterances(
        embeddings, data
    )

    logger.info(f"Original count: {len(embeddings)}")
    logger.info(f"Filtered count: {len(filtered_embeddings)}")
    logger.info(
        f"Filtering ratio: {len(filtered_embeddings)/len(embeddings):.2%}")

    # Show some examples of filtered out utterances
    unimportant_mask = importance_scores < predictor.threshold
    unimportant_indices = np.where(unimportant_mask)[
        0][:50]  # First 10 unimportant

    logger.info("\nSample unimportant utterances (filtered out):")
    for idx in unimportant_indices:
        text = data.iloc[idx]['text']
        score = importance_scores[idx]
        logger.info(f"  Score: {score:.3f} - Text: {text[::-1]}...")

    logger.info("\nSample important utterances (kept):")
    for idx in important_indices[:60]:  # First 10 important
        text = data.iloc[idx]['text']
        score = importance_scores[idx]
        logger.info(f"  Score: {score:.3f} - Text: {text[::-1]}...")

    return True


def test_full_pipeline():
    """Test the full pipeline with filtering enabled."""
    from processing.clusterer import Clusterer

    logger.info("Testing full clustering pipeline with filtering...")

    # Create output directory for test
    test_output_dir = PROJECT_ROOT / "test_clustering_results"
    test_output_dir.mkdir(exist_ok=True)

    # Initialize clusterer with filtering enabled
    clusterer = Clusterer(
        embeddings_file='utterance_embeddings.npy',
        data_file='utterances_data.pkl',
        output_dir=str(test_output_dir),
        filter_unimportant=True
    )

    # Load data (this will apply filtering)
    embeddings, data = clusterer.load_data()

    logger.info(f"After filtering - Embeddings shape: {embeddings.shape}")
    if hasattr(clusterer, 'importance_scores') and clusterer.original_embeddings is not None:
        logger.info(
            f"Filtering ratio: {len(embeddings)/len(clusterer.original_embeddings):.2%}")

    # Test clustering
    clusterer.cluster_npy_file(clusters_num=30, sample_size=5000)

    clusterer.visualize_clusters_2d()
    logger.info("Full pipeline test completed successfully!")

    return True


if __name__ == "__main__":
    try:
        logger.info("Starting importance filtering tests...")

        # Test predictor
        test_predictor()

        # Test full pipeline
        test_full_pipeline()

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
