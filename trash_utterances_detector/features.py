"""
Feature extraction utilities for trash utterances detection.
This module contains shared functionality for creating handcrafted features
used in both training and prediction.
"""

import re
import numpy as np
from pathlib import Path
from typing import List, Union
from utils.logger_config import get_logger

logger = get_logger(__name__)

# Path constants
PROJECT_ROOT = Path(__file__).parent.parent
TRASH_DETECTOR_DIR = PROJECT_ROOT / "trash_utterances_detector"

# Data file names
EMBEDDINGS_FILE = "embeddings.npy"
SENTENCES_FILE = "sentences.npy"
LABELS_FILE = "labels.npy"
LABELS_CSV_FILE = "labels_to_fill.csv"
CLASSIFIER_FILE = "classifier.pkl"

# Hebrew procedural content patterns
PROCEDURAL_PATTERNS = [
    r"\b(תודה|מי בעד|מי נגד|נמשיך מחר|הישיבה נעולה|אושרה|אושר|נוכח|הצבעה|ישיבה|קריאות|קריאה)\b"
]

# Feature configuration
FEATURE_MULTIPLIER = 500
NUM_FEATURE_COPIES = 12  # Number of times to repeat the unimportant_score


def contains_procedural_content(text: str) -> bool:
    """
    Check if text contains procedural content based on Hebrew patterns.

    Args:
        text: Text to analyze

    Returns:
        bool: True if text contains procedural content
    """
    if not text:
        return False

    for pattern in PROCEDURAL_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def calculate_word_penalty(text: str) -> float:
    """
    Calculate penalty based on number of words (shorter text gets higher penalty).

    Args:
        text: Text to analyze

    Returns:
        float: Penalty score (1/number_of_words)
    """
    if not text or not text.strip():
        return 1.0

    word_count = len(text.strip().split())
    return 1.0 / max(word_count, 1)  # Avoid division by zero


def calculate_unimportance_score(text: str) -> float:
    """
    Calculate unimportance score based on procedural content and word count.

    Args:
        text: Text to analyze

    Returns:
        float: Unimportance score
    """
    procedural_score = int(contains_procedural_content(text))
    word_penalty = calculate_word_penalty(text)

    return (procedural_score + word_penalty) * FEATURE_MULTIPLIER


def make_handcrafted_features(texts: Union[List[str], np.ndarray]) -> np.ndarray:
    """
    Create handcrafted features for utterance importance classification.

    This function creates features based on:
    1. Whether the text contains procedural content (Hebrew patterns)
    2. Word count penalty (shorter texts are more likely to be unimportant)

    The unimportance score is repeated multiple times to make it stand out
    among the normalized embedding features.

    Args:
        texts: List or array of text strings to process

    Returns:
        numpy.ndarray: Array of shape (n_samples, NUM_FEATURE_COPIES) containing
                      handcrafted features
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, NUM_FEATURE_COPIES)

    # Handle numpy arrays with dtype=object
    if isinstance(texts, np.ndarray):
        texts = texts.tolist()

    features = []

    for text in texts:
        # Handle None or non-string values
        text_str = str(text) if text is not None else ""
        unimportance_score = calculate_unimportance_score(text_str)

        # Repeat the score multiple times to create feature vector
        # This helps the feature stand out among the 700+ normalized embedding features
        feature_vector = [unimportance_score] * NUM_FEATURE_COPIES
        features.append(feature_vector)

    logger.debug("Created handcrafted features for %d texts", len(texts))

    return np.array(features, dtype=np.float32)


def get_training_dir() -> Path:
    """
    Get the training directory path.

    Returns:
        Path: Path to the training directory
    """
    return TRASH_DETECTOR_DIR


def get_data_file_paths() -> dict:
    """
    Get paths to all data files used in training/prediction.

    Returns:
        dict: Dictionary with file names as keys and paths as values
    """
    training_dir = get_training_dir()
    return {
        'embeddings': training_dir / EMBEDDINGS_FILE,
        'sentences': training_dir / SENTENCES_FILE,
        'labels': training_dir / LABELS_FILE,
        'labels_csv': training_dir / LABELS_CSV_FILE,
        'classifier': training_dir / CLASSIFIER_FILE,
        'training_dir': training_dir
    }


def get_feature_info() -> dict:
    """
    Get information about the handcrafted features.

    Returns:
        dict: Information about feature configuration
    """
    return {
        'num_features': NUM_FEATURE_COPIES,
        'feature_multiplier': FEATURE_MULTIPLIER,
        'procedural_patterns': PROCEDURAL_PATTERNS,
        'description': 'Handcrafted features based on procedural content detection and word count penalty'
    }
