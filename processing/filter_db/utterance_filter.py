"""
Utterance filtering module for filtering out low-importance utterances.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from utils.logger_config import get_logger
from trash_utterances_detector.predictor import UtteranceImportancePredictor
from .filtered_storage import FilteredUtteranceStorage
from . import FilterReportGenerator

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


def get_default_threshold() -> float:
    """Get the default threshold from the trained model."""
    predictor = UtteranceImportancePredictor()
    return predictor.threshold or 0.5


def filter_and_save_utterances(embeddings: np.ndarray, df: pd.DataFrame, threshold: float | None = None) -> tuple[np.ndarray, pd.DataFrame]:
    """Filter utterances by importance and save all data."""
    # Get scores and threshold
    predictor = UtteranceImportancePredictor()
    if threshold is None:
        threshold = predictor.threshold or 0.5
        logger.info("Using model's trained threshold: %s", threshold)

    scores, _ = predictor.predict_importance(embeddings, df['text'].tolist())

    keep_mask = scores >= threshold
    filter_mask = scores < threshold

    logger.info("Keeping %d/%d utterances (threshold: %s)",
                np.sum(keep_mask), len(scores), threshold)
    logger.info("Filtering out %d utterances (%.1f%%)",
                np.sum(filter_mask), np.mean(filter_mask)*100)

    filtered_embeddings = embeddings[keep_mask]
    filtered_df = df.iloc[np.where(keep_mask)[0]].copy()
    filtered_df['original_index'] = filtered_df.index
    filtered_df['importance_score'] = scores[keep_mask]

    storage = FilteredUtteranceStorage(PROJECT_ROOT)
    storage.save_filtered_embeddings(filtered_embeddings)
    storage.save_filtered_df(filtered_df)

    if np.sum(filter_mask) > 0:
        filtered_out_sorted = storage.save_filtered_utterances(
            df, scores, filter_mask, threshold)
        report_generator = FilterReportGenerator(PROJECT_ROOT)
        report_generator.generate_summary_report(
            filtered_out_sorted, threshold, scores[filter_mask])

    return filtered_embeddings, filtered_df


def get_or_create_filtered_data(embeddings: np.ndarray, df: pd.DataFrame, threshold: float, force_refresh: bool = False) -> tuple[np.ndarray, pd.DataFrame]:
    """Get existing filtered data or create new filtered data if needed."""
    storage = FilteredUtteranceStorage(PROJECT_ROOT)

    if force_refresh or not storage.embeddings_exist() or not storage.filtered_df_exists():
        logger.info("Creating filtered data...")
        return filter_and_save_utterances(embeddings, df, threshold)

    logger.info("Loading existing filtered data...")
    filtered_embeddings = storage.load_filtered_embeddings()
    filtered_df = storage.load_filtered_df()

    logger.info(
        f"Filtered data - DataFrame shape: {filtered_df.shape}, Embeddings shape: {filtered_embeddings.shape}")
    return filtered_embeddings, filtered_df


def validate_filtered_json(threshold: float | None = None):
    """Validate and display info about the filtered JSON file."""
    if threshold is None:
        threshold = get_default_threshold()
        logger.info(
            "Using model's trained threshold for validation: %s", threshold)

    report_generator = FilterReportGenerator(PROJECT_ROOT)
    report_generator.validate_filtered_json(threshold)


def get_filtered_stats(threshold: float | None = None) -> dict:
    """Get statistics about filtered utterances."""
    if threshold is None:
        threshold = get_default_threshold()

    report_generator = FilterReportGenerator(PROJECT_ROOT)
    return report_generator.get_filtered_stats(threshold)
