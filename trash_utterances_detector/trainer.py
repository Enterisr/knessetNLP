"""
Simple importance classifier based on provided code structure.
This script creates NPY files and trains logistic regression.
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_recall_curve, recall_score, precision_score
from utils.logger_config import get_logger
from .features import make_handcrafted_features, get_feature_info, get_data_file_paths

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


def create_training_files():
    """
    Create NPY files for training from existing data.
    """
    logger.info("Creating training files...")

    embeddings = np.load(PROJECT_ROOT / "utterance_embeddings.npy")
    data = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")

    n_samples = 1000
    indices = np.random.choice(len(embeddings), n_samples, replace=False)

    sample_embeddings = embeddings[indices]
    sample_texts = [data.iloc[i]['text'] for i in indices]

    file_paths = get_data_file_paths()
    training_dir = file_paths['training_dir']
    training_dir.mkdir(exist_ok=True)

    np.save(file_paths['embeddings'], sample_embeddings)
    np.save(file_paths['sentences'], np.array(sample_texts, dtype=object))

    labels = np.full(n_samples, '')
    np.save(file_paths['labels'], labels)

    df = pd.DataFrame({
        'index': range(n_samples),
        'text': sample_texts,
        'label': labels
    })
    df.to_csv(file_paths['labels_csv'], index=False, encoding='utf-8')

    logger.info(f"Created training files in {training_dir}")
    logger.info(
        "Please fill the labels in labels_to_fill.csv with 1 (important) or 0 (not important)")
    logger.info("Then update labels.npy with the labeled data")


# Note: make_handcrafted_features is now imported from .features module


def load_and_use_csv_labels():
    """
    Load labels from CSV and update the NPY file.
    """
    file_paths = get_data_file_paths()

    if not file_paths['labels_csv'].exists():
        logger.error("CSV file not found. Run create_training_files() first.")
        return

    df = pd.read_csv(file_paths['labels_csv'], encoding='utf-8')

    labeled_df = df[df['label'].notna() & (df['label'] != -1)]

    if len(labeled_df) == 0:
        logger.error("No labels found in CSV. Please fill the 'label' column.")
        return

    labels = np.full(len(df), -1)
    for idx, row in labeled_df.iterrows():
        labels[row['index']] = int(row['label'])

    np.save(file_paths['labels'], labels)
    logger.info(f"Updated labels.npy with {len(labeled_df)} labeled samples")


def add_more_training_samples(n_additional=500):
    """
    Add more samples to existing training data.
    """
    logger.info(f"Adding {n_additional} more training samples...")

    file_paths = get_data_file_paths()

    # Load existing data
    existing_embeddings = np.load(file_paths['embeddings'])
    existing_sentences = np.load(file_paths['sentences'], allow_pickle=True)
    existing_labels = np.load(file_paths['labels'], allow_pickle=True)
    existing_csv = pd.read_csv(file_paths['labels_csv'], encoding='utf-8')

    # Load full dataset
    all_embeddings = np.load(PROJECT_ROOT / "utterance_embeddings.npy")
    all_data = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")

    # Get indices that are not already used
    existing_indices = set(range(len(existing_embeddings)))
    available_indices = [i for i in range(
        len(all_embeddings)) if i not in existing_indices]

    if len(available_indices) < n_additional:
        logger.warning(
            f"Only {len(available_indices)} samples available, using all of them")
        n_additional = len(available_indices)

    # Sample new indices
    new_indices = np.random.choice(
        available_indices, n_additional, replace=False)

    # Get new samples
    new_embeddings = all_embeddings[new_indices]
    new_texts = [all_data.iloc[i]['text'] for i in new_indices]
    new_labels = np.full(n_additional, '')

    # Combine with existing
    combined_embeddings = np.concatenate([existing_embeddings, new_embeddings])
    combined_sentences = np.concatenate(
        [existing_sentences, np.array(new_texts, dtype=object)])
    combined_labels = np.concatenate([existing_labels, new_labels])

    # Create new CSV data
    new_csv_rows = pd.DataFrame({
        'index': range(len(existing_csv), len(existing_csv) + n_additional),
        'text': new_texts,
        'label': new_labels
    })

    combined_csv = pd.concat([existing_csv, new_csv_rows], ignore_index=True)

    # Save updated files
    np.save(file_paths['embeddings'], combined_embeddings)
    np.save(file_paths['sentences'], combined_sentences)
    np.save(file_paths['labels'], combined_labels)
    combined_csv.to_csv(file_paths['labels_csv'],
                        index=False, encoding='utf-8')

    logger.info(
        f"Added {n_additional} samples. Total samples: {len(combined_embeddings)}")
    logger.info(f"Updated CSV file with new samples to label")


def _load_training_data():
    """Load and prepare training data."""
    file_paths = get_data_file_paths()

    X_emb = np.load(file_paths['embeddings'])
    y = np.load(file_paths['labels'])
    texts = np.load(file_paths['sentences'], allow_pickle=True)

    logger.info(f"Training with {len(y)} labeled samples")
    logger.info(f"Label distribution: {np.bincount(y)}")

    handcrafted_feats = make_handcrafted_features(texts)
    X = np.concatenate([X_emb, handcrafted_feats], axis=1)

    return X, y, file_paths


def _create_classifier():
    """Create and return a configured LogisticRegression classifier."""
    return LogisticRegression(
        max_iter=3000,
        C=.02,
        random_state=501,
        class_weight='balanced'  # Handle class imbalance
    )


def _find_optimal_threshold(y_val, probs, min_recall=0.7):
    """Find optimal threshold balancing precision and recall."""
    prec, rec, thr = precision_recall_curve(y_val, probs)

    recall_mask = rec >= min_recall

    if np.any(recall_mask):
        # Among points with acceptable recall, find the one with highest precision
        valid_indices = np.where(recall_mask)[0]
        best_prec_idx = valid_indices[np.argmax(prec[recall_mask])]
        best_threshold = thr[best_prec_idx]
    else:
        # Fallback: use F1 optimization if no point meets minimum recall
        f1_scores = 2 * (prec * rec) / (prec + rec + 1e-8)
        best_f1_idx = np.argmax(f1_scores)
        best_threshold = thr[best_f1_idx]

    return best_threshold


def _evaluate_fold(clf, X_val, y_val):
    """Evaluate a single fold and return metrics."""
    probs = clf.predict_proba(X_val)[:, 1]
    best_threshold = _find_optimal_threshold(y_val, probs)
    predictions = (probs >= best_threshold).astype(int)

    fold_recall = recall_score(y_val, predictions)
    fold_precision = precision_score(y_val, predictions, zero_division=0)
    fold_f1 = 2 * (fold_precision * fold_recall) / \
        (fold_precision + fold_recall + 1e-8)

    return {
        'recall': fold_recall,
        'precision': fold_precision,
        'f1': fold_f1,
        'threshold': best_threshold
    }


def _perform_kfold_validation(X, y, k_folds=5):
    """Perform k-fold cross-validation and return results."""
    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)

    fold_results = []
    logger.info(f"Starting {k_folds}-fold cross-validation...")

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        logger.info(f"Training fold {fold}/{k_folds}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        clf = _create_classifier()
        clf.fit(X_train, y_train)

        fold_metrics = _evaluate_fold(clf, X_val, y_val)
        fold_results.append(fold_metrics)

        logger.info(f"Fold {fold} - Threshold: {fold_metrics['threshold']:.3f}, "
                    f"Precision: {fold_metrics['precision']:.3f}, "
                    f"Recall: {fold_metrics['recall']:.3f}, "
                    f"F1: {fold_metrics['f1']:.3f}")

    return fold_results


def _calculate_cv_statistics(fold_results):
    """Calculate cross-validation statistics from fold results."""
    recalls = [result['recall'] for result in fold_results]
    precisions = [result['precision'] for result in fold_results]
    f1_scores = [result['f1'] for result in fold_results]
    thresholds = [result['threshold'] for result in fold_results]

    return {
        'mean_recall': np.mean(recalls),
        'std_recall': np.std(recalls),
        'mean_precision': np.mean(precisions),
        'std_precision': np.std(precisions),
        'mean_f1': np.mean(f1_scores),
        'std_f1': np.std(f1_scores),
        'mean_threshold': np.mean(thresholds),
        'k_folds': len(fold_results)
    }


def _log_cv_results(stats):
    """Log cross-validation results in a formatted way."""
    logger.info("\n" + "="*50)
    logger.info("K-FOLD CROSS-VALIDATION RESULTS")
    logger.info("="*50)
    logger.info(
        f"Recall:     {stats['mean_recall']:.3f} ± {stats['std_recall']:.3f}")
    logger.info(
        f"Precision:  {stats['mean_precision']:.3f} ± {stats['std_precision']:.3f}")
    logger.info(f"F1 Score:   {stats['mean_f1']:.3f} ± {stats['std_f1']:.3f}")
    logger.info(f"Avg Threshold: {stats['mean_threshold']:.3f}")
    logger.info("="*50)


def _train_and_save_final_model(X, y, threshold, file_paths, cv_stats):
    """Train final model on all data and save it."""
    logger.info("Training final model on all data...")

    final_clf = _create_classifier()
    final_clf.fit(X, y)

    model_data = {
        'model': final_clf,
        'threshold': threshold,
        'kfold_stats': cv_stats
    }

    model_path = file_paths['classifier']
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    logger.info(f"Final model saved to {model_path}")
    return final_clf


def train_classifier_with_kfold():
    """
    Train classifier with k-fold cross-validation for more robust evaluation.
    """
    # Load and prepare data
    X, y, file_paths = _load_training_data()

    # Perform k-fold cross-validation
    fold_results = _perform_kfold_validation(X, y)

    # Calculate and log statistics
    cv_stats = _calculate_cv_statistics(fold_results)
    _log_cv_results(cv_stats)

    # Train and save final model
    final_clf = _train_and_save_final_model(
        X, y, cv_stats['mean_threshold'], file_paths, cv_stats
    )

    # Return results (excluding k_folds from return dict for backward compatibility)
    return final_clf, cv_stats['mean_threshold'], {
        'mean_recall': cv_stats['mean_recall'],
        'std_recall': cv_stats['std_recall'],
        'mean_precision': cv_stats['mean_precision'],
        'std_precision': cv_stats['std_precision'],
        'mean_f1': cv_stats['mean_f1'],
        'std_f1': cv_stats['std_f1'],
    }
