"""
Storage utilities for filtered utterances.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from utils.logger_config import get_logger

logger = get_logger(__name__)


class FilteredUtteranceStorage:
    """Handles storage and retrieval of filtered utterances."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def save_filtered_utterances(self, df: pd.DataFrame, scores: np.ndarray, filter_mask: np.ndarray, threshold: float) -> pd.DataFrame:
        """Save filtered out utterances to JSON file."""
        if not np.sum(filter_mask):
            return pd.DataFrame()

        filtered_out = df[filter_mask].copy()
        filtered_out['importance_score'] = scores[filter_mask]
        filtered_out_sorted = filtered_out.sort_values(
            'importance_score', ascending=False)

        path = self.project_root / f"filtered_out_utterances_{threshold}.json"
        filtered_out_sorted.to_json(
            str(path), orient='records', indent=2, force_ascii=False)

        logger.info("Saved %d filtered out utterances, score range: %.3f - %.3f",
                    len(filtered_out_sorted), scores[filter_mask].min(), scores[filter_mask].max())
        return filtered_out_sorted

    def save_filtered_embeddings(self, embeddings: np.ndarray):
        """Save filtered embeddings to numpy file."""
        path = self.project_root / "filtered_utterance_embeddings.npy"
        np.save(path, embeddings)
        logger.info("Saved %d filtered embeddings", len(embeddings))
        
    def save_filtered_df(self, df: pd.DataFrame):
        """Save filtered DataFrame to pickle file."""
        path = self.project_root / "filtered_utterances_data.pkl"
        df.to_pickle(path)
        logger.info("Saved filtered DataFrame with %d rows", len(df))

    def load_filtered_utterances(self, threshold: float) -> pd.DataFrame:
        """Load filtered out utterances from JSON file."""
        return self._load_json(self.project_root / f"filtered_out_utterances_{threshold}.json")

    def load_filtered_embeddings(self) -> np.ndarray:
        """Load filtered embeddings from numpy file."""
        path = self.project_root / "filtered_utterance_embeddings.npy"
        return np.load(path) if path.exists() else np.array([])
        
    def load_filtered_df(self) -> pd.DataFrame:
        """Load filtered DataFrame from pickle file."""
        path = self.project_root / "filtered_utterances_data.pkl"
        if path.exists():
            df = pd.read_pickle(path)
            logger.info("Loaded filtered DataFrame with %d rows", len(df))
            return df
        return pd.DataFrame()

    def filtered_df_exists(self) -> bool:
        """Check if filtered DataFrame exists."""
        return (self.project_root / "filtered_utterances_data.pkl").exists()

    def embeddings_exist(self) -> bool:
        """Check if filtered embeddings exist."""
        return (self.project_root / "filtered_utterance_embeddings.npy").exists()

    def _load_json(self, path: Path) -> pd.DataFrame:
        """Load JSON file with error handling."""
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_json(str(path), orient='records')
        except Exception:
            return pd.DataFrame()
