"""
Storage utilities for filtered utterances.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple
from utils.logger_config import get_logger

logger = get_logger(__name__)


class FilteredUtteranceStorage:
    """Handles storage and retrieval of filtered utterances."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def save_filtered_utterances(self, df: pd.DataFrame, scores: np.ndarray,
                                 filter_mask: np.ndarray, threshold: float) -> pd.DataFrame:
        """Save filtered utterances to JSON file, sorted by score."""
        if not np.sum(filter_mask):
            logger.info("No utterances to filter out")
            return pd.DataFrame()

        filtered_out = df[filter_mask].copy()
        filtered_out['importance_score'] = scores[filter_mask]

        # Sort by importance score (descending - highest scores first)
        filtered_out_sorted = filtered_out.sort_values(
            'importance_score', ascending=False)

        output_path = self.project_root / \
            f"filtered_out_utterances_{threshold}.json"

        # Convert to clean JSON format (already sorted)
        filtered_out_sorted.to_json(
            str(output_path), orient='records', indent=2, force_ascii=False)

        logger.info(
            "Saved %d filtered utterances to %s (sorted by score)",
            len(filtered_out_sorted), output_path
        )
        logger.info(
            "Score range: %.3f - %.3f",
            scores[filter_mask].min(), scores[filter_mask].max()
        )

        return filtered_out_sorted

    def load_filtered_utterances(self, threshold: float) -> pd.DataFrame:
        """Load filtered utterances from JSON file."""
        output_path = self.project_root / \
            f"filtered_out_utterances_{threshold}.json"

        if not output_path.exists():
            logger.warning("Filtered file not found: %s", output_path)
            return pd.DataFrame()

        try:
            return pd.read_json(str(output_path), orient='records')
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error loading filtered utterances: %s", e)
            return pd.DataFrame()
