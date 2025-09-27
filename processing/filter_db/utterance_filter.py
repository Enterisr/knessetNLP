"""
Utterance filtering module for filtering out low-importance utterances.
"""

import numpy as np
from pathlib import Path
from utils.logger_config import get_logger
from trash_utterances_detector.predictor import UtteranceImportancePredictor
from . import FilterReportGenerator, FilteredUtteranceStorage

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


def get_default_threshold() -> float:
    """Get the default threshold from the trained model."""
    predictor = UtteranceImportancePredictor()
    return predictor.threshold or 0.5  # fallback to 0.5 if threshold is None


def _get_importance_scores(embeddings: np.ndarray, texts: list, threshold: float | None = None) -> tuple[np.ndarray, float]:
    """Get importance scores and threshold from predictor."""
    predictor = UtteranceImportancePredictor()

    if threshold is None:
        threshold = predictor.threshold or 0.5
        logger.info("Using model's trained threshold: %s", threshold)

    scores, _ = predictor.predict_importance(embeddings, texts)
    return scores, threshold


def _log_filtering_stats(scores: np.ndarray, threshold: float, keep_mask: np.ndarray, filter_mask: np.ndarray):
    """Log filtering statistics."""
    logger.info(
        "Keeping %d/%d utterances (threshold: %s)",
        np.sum(keep_mask), len(scores), threshold
    )
    logger.info(
        "Filtering out %d utterances (%.1f%%)",
        np.sum(filter_mask), np.mean(filter_mask)*100
    )


def _save_filtered_out_utterances(df, scores: np.ndarray, filter_mask: np.ndarray, threshold: float):
    """Save filtered out utterances and generate reports."""
    if np.sum(filter_mask) == 0:
        return

    storage = FilteredUtteranceStorage(PROJECT_ROOT)
    report_generator = FilterReportGenerator(PROJECT_ROOT)

    filtered_out_sorted = storage.save_filtered_utterances(
        df, scores, filter_mask, threshold
    )
    report_generator.generate_summary_report(
        filtered_out_sorted, threshold, scores[filter_mask]
    )


def _prepare_filtered_dataset(embeddings: np.ndarray, df, scores: np.ndarray, keep_mask: np.ndarray) -> tuple:
    """Prepare and save filtered dataset."""
    filtered_embeddings = embeddings[keep_mask]
    filtered_df = df[keep_mask].copy()
    filtered_df['original_index'] = filtered_df.index
    filtered_df['importance_score'] = scores[keep_mask]
    filtered_df = filtered_df.reset_index(drop=True)

    # Save filtered data
    filtered_embeddings_path = PROJECT_ROOT / "filtered_utterance_embeddings.npy"
    filtered_df_path = PROJECT_ROOT / "filtered_utterances_data.pkl"

    np.save(filtered_embeddings_path, filtered_embeddings)
    filtered_df.to_pickle(filtered_df_path)

    logger.info("Saved filtered embeddings to %s", filtered_embeddings_path)
    logger.info("Saved filtered dataframe to %s", filtered_df_path)

    return filtered_embeddings, filtered_df


def filter_and_save_utterances(embeddings: np.ndarray, df, threshold: float | None = None) -> tuple:
    """Filter utterances by importance and save filtered out ones."""
    # Get importance scores
    scores, threshold = _get_importance_scores(
        embeddings, df['text'].tolist(), threshold)

    # Create masks
    keep_mask = scores >= threshold
    filter_mask = scores < threshold

    # Log statistics
    _log_filtering_stats(scores, threshold, keep_mask, filter_mask)

    # Save filtered out utterances
    _save_filtered_out_utterances(df, scores, filter_mask, threshold)

    # Prepare and save filtered dataset
    filtered_embeddings, filtered_df = _prepare_filtered_dataset(
        embeddings, df, scores, keep_mask)

    logger.info("Preserved original indices and importance scores in dataframe")
    return filtered_embeddings, filtered_df


def validate_filtered_json(threshold: float | None = None):
    """Validate and display info about the filtered JSON file."""
    # Use predictor's default threshold if none provided
    if threshold is None:
        predictor = UtteranceImportancePredictor()
        threshold = predictor.threshold or 0.5
        logger.info(
            "Using model's trained threshold for validation: %s", threshold)

    report_generator = FilterReportGenerator(PROJECT_ROOT)
    report_generator.validate_filtered_json(threshold)


def get_filtered_stats(threshold: float | None = None) -> dict:
    """Get statistics about filtered utterances."""
    # Use predictor's default threshold if none provided
    if threshold is None:
        predictor = UtteranceImportancePredictor()
        threshold = predictor.threshold or 0.5

    report_generator = FilterReportGenerator(PROJECT_ROOT)
    return report_generator.get_filtered_stats(threshold)
