"""
Trash utterances detector module.

This module provides tools for training and using a classifier to determine
if Knesset utterances are important or not (filtering out "trash" utterances).
"""

from .trainer import train_classifier_with_kfold
from .predictor import UtteranceImportancePredictor
from .features import make_handcrafted_features, get_feature_info, get_data_file_paths, get_training_dir

__all__ = [
    'train_classifier_with_kfold',
    'UtteranceImportancePredictor',
    'make_handcrafted_features',
    'get_feature_info',
    'get_data_file_paths',
    'get_training_dir'
]
