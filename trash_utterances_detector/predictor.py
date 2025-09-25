"""
Predictor module for filtering out unimportant utterances using trained classifier.
"""

import numpy as np
import pickle
from pathlib import Path
from utils.logger_config import get_logger
from .features import make_handcrafted_features, get_feature_info, get_data_file_paths

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


class UtteranceImportancePredictor:
    """Predicts importance of utterances using trained classifier."""

    def __init__(self, model_path: str | None = None):
        """
        Initialize predictor with trained model.

        Args:
            model_path: Path to the trained classifier pickle file.
                       If None, uses default classifier.pkl
        """
        if model_path is None:
            file_paths = get_data_file_paths()
            self.model_path = file_paths['classifier']
        else:
            self.model_path = model_path
        self.model = None
        self.threshold = None
        self.kfold_stats = None
        self._load_model()

    def _load_model(self):
        """Load the trained classifier model."""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)

            if isinstance(model_data, dict):
                self.model = model_data['model']
                self.threshold = model_data.get('threshold', 0.5)
                self.kfold_stats = model_data.get('kfold_stats', {})
            else:
                # Handle old format where only model was saved
                self.model = model_data
                self.threshold = 0.5

            logger.info(f"Loaded classifier from {self.model_path}")
            logger.info(f"Using threshold: {self.threshold}")

            if self.kfold_stats:
                logger.info(f"Model stats - Recall: {self.kfold_stats.get('mean_recall', 'N/A'):.3f}, "
                            f"Precision: {self.kfold_stats.get('mean_precision', 'N/A'):.3f}, "
                            f"F1: {self.kfold_stats.get('mean_f1', 'N/A'):.3f}")

            # Log feature information
            feature_info = get_feature_info()
            logger.info(
                f"Using {feature_info['num_features']} handcrafted features")

        except Exception as e:
            logger.error(f"Failed to load model from {self.model_path}: {e}")
            raise

    # Note: make_handcrafted_features is now imported from .features module

    def predict_importance(self, embeddings, texts):
        """
        Predict importance scores for utterances.

        Args:
            embeddings: numpy array of utterance embeddings
            texts: list of utterance texts

        Returns:
            tuple: (importance_scores, important_mask)
                  importance_scores: probability scores for being important
                  important_mask: boolean mask where True means important
        """
        if self.model is None:
            raise ValueError("Model not loaded. Cannot make predictions.")

        # Create handcrafted features
        handcrafted_feats = make_handcrafted_features(texts)

        # Combine embeddings with handcrafted features
        X = np.concatenate([embeddings, handcrafted_feats], axis=1)

        # Get probability scores
        importance_scores = self.model.predict_proba(
            X)[:, 1]  # Probability of being important

        # Apply threshold to get binary predictions
        important_mask = importance_scores >= self.threshold

        logger.info(f"Classified {len(texts)} utterances")
        logger.info(
            f"Important utterances: {np.sum(important_mask)} ({np.mean(important_mask)*100:.1f}%)")
        logger.info(
            f"Unimportant utterances: {np.sum(~important_mask)} ({np.mean(~important_mask)*100:.1f}%)")

        return importance_scores, important_mask

    def filter_important_utterances(self, embeddings, data):
        """
        Filter data to keep only important utterances.

        Args:
            embeddings: numpy array of utterance embeddings
            data: pandas DataFrame or dict with utterance data

        Returns:
            tuple: (filtered_embeddings, filtered_data, importance_scores, important_indices)
        """
        import pandas as pd

        # Handle both DataFrame and dict inputs
        if isinstance(data, dict):
            texts = data['text'] if isinstance(
                data['text'], list) else data['text'].tolist()
        else:
            texts = data['text'].tolist()

        # Get importance predictions
        importance_scores, important_mask = self.predict_importance(
            embeddings, texts)

        # Filter embeddings
        filtered_embeddings = embeddings[important_mask]

        # Filter data
        if isinstance(data, dict):
            filtered_data = {}
            for key, values in data.items():
                if isinstance(values, list):
                    filtered_data[key] = [values[i]
                                          for i in range(len(values)) if important_mask[i]]
                elif hasattr(values, 'iloc'):  # pandas Series
                    filtered_data[key] = values.iloc[important_mask].reset_index(
                        drop=True)
                else:
                    filtered_data[key] = values
        else:
            filtered_data = data[important_mask].reset_index(drop=True)

        important_indices = np.where(important_mask)[0]

        logger.info(
            f"Filtered from {len(embeddings)} to {len(filtered_embeddings)} utterances")

        return filtered_embeddings, filtered_data, importance_scores, important_indices
