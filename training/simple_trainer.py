"""
Simple importance classifier based on provided code structure.
This script creates NPY files and trains logistic regression.
"""

import numpy as np
import pandas as pd
import pickle
import re
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, precision_recall_curve, recall_score, precision_score
from utils.logger_config import get_logger

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


def create_training_files():
    """
    Create NPY files for training from existing data.
    """
    logger.info("Creating training files...")

    # Load existing embeddings and data
    embeddings = np.load(PROJECT_ROOT / "utterance_embeddings.npy")
    data = pd.read_pickle(PROJECT_ROOT / "utterances_data.pkl")

    # Create sample for labeling (you'll need to manually label these)
    n_samples = 1000
    indices = np.random.choice(len(embeddings), n_samples, replace=False)

    sample_embeddings = embeddings[indices]
    sample_texts = [data.iloc[i]['text'] for i in indices]

    # Save sample data
    training_dir = PROJECT_ROOT / "training"
    training_dir.mkdir(exist_ok=True)

    np.save(training_dir / "embeddings.npy", sample_embeddings)
    np.save(training_dir / "sentences.npy",
            np.array(sample_texts, dtype=object))

    # Create empty labels file (you need to fill this manually)
    labels = np.full(n_samples, '')  # -1 means unlabeled
    np.save(training_dir / "labels.npy", labels)

    # Create CSV for easier labeling
    df = pd.DataFrame({
        'index': range(n_samples),
        # Reverse Hebrew for readability
        'text': sample_texts,
        'label': labels
    })
    df.to_csv(training_dir / "labels_to_fill.csv",
              index=False, encoding='utf-8')

    logger.info(f"Created training files in {training_dir}")
    logger.info(
        "Please fill the labels in labels_to_fill.csv with 1 (important) or 0 (not important)")
    logger.info("Then update labels.npy with the labeled data")


def make_handcrafted_features(texts):
    """
    Create handcrafted features as in the original code.
    """
    import re
    feats = []
    for t in texts:
        t0 = t or ""
        has_num = int(bool(re.search(r"\d", t0)))
        has_money = int(("₪" in t0) or bool(
            re.search(r"\b(אלפים|מיליונ|תקציב)\b", t0)))
        procedural = int(
            bool(re.search(r"\b(תודה|מי בעד|מי נגד|נמשיך מחר|הישיבה נעולה)\b", t0)))
        feats.append([has_num, has_money, procedural])
    return np.array(feats, dtype=np.float32)


def load_and_use_csv_labels():
    """
    Load labels from CSV and update the NPY file.
    """
    training_dir = PROJECT_ROOT / "training"
    csv_path = training_dir / "labels_to_fill.csv"

    if not csv_path.exists():
        logger.error("CSV file not found. Run create_training_files() first.")
        return

    # Load CSV
    df = pd.read_csv(csv_path, encoding='utf-8')

    # Check for labeled data
    labeled_df = df[df['label'].notna() & (df['label'] != -1)]

    if len(labeled_df) == 0:
        logger.error("No labels found in CSV. Please fill the 'label' column.")
        return

    # Update labels.npy
    labels = np.full(len(df), -1)
    for idx, row in labeled_df.iterrows():
        labels[row['index']] = int(row['label'])

    np.save(training_dir / "labels.npy", labels)
    logger.info(f"Updated labels.npy with {len(labeled_df)} labeled samples")


def train_classifier_with_kfold():
    """
    Train classifier with k-fold cross-validation for more robust evaluation.
    """
    training_dir = PROJECT_ROOT / "training"

    # Load data
    X_emb = np.load(training_dir / "embeddings.npy")
    y = np.load(training_dir / "labels.npy")
    texts = np.load(training_dir / "sentences.npy", allow_pickle=True)

    # Check if labels are filled
    if np.all(y == -1):
        logger.error(
            "No labels found! Please fill the labels.npy file or use the CSV file.")
        return None

    # Filter only labeled data
    labeled_mask = y != -1
    X_emb = X_emb[labeled_mask]
    y = y[labeled_mask]
    texts = texts[labeled_mask]

    logger.info(f"Training with {len(y)} labeled samples")
    logger.info(f"Label distribution: {np.bincount(y.astype(int))}")

    # handcrafted features
    X_feats = make_handcrafted_features(texts)
    X = np.hstack([X_emb, X_feats])

    # K-fold cross-validation
    k_folds = 5
    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)

    # Metrics to track across folds
    fold_recalls = []
    fold_precisions = []
    fold_f1_scores = []
    fold_thresholds = []

    min_recall = 0.9

    logger.info(f"Starting {k_folds}-fold cross-validation...")

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        logger.info(f"Training fold {fold}/{k_folds}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Use class weights that heavily penalize false negatives
        class_weights = {0: 1.0, 1: 3.0}
        clf = LogisticRegression(
            # L2 regularization (smaller = stronger regularization)
            max_iter=2000, class_weight=class_weights, n_jobs=-1, random_state=42,
            C=0.2,
            penalty='l2',
            solver='liblinear'
        )
        clf.fit(X_train, y_train)

        # Get predictions and probabilities
        probs = clf.predict_proba(X_val)[:, 1]

        # Find best threshold using precision-recall curve
        prec, rec, thr = precision_recall_curve(y_val, probs)

        # Find threshold that achieves minimum recall
        recall_mask = rec >= min_recall
        if np.any(recall_mask):
            # Among thresholds that achieve min_recall, pick the one with best precision
            valid_indices = np.where(recall_mask)[0]
            best_prec_idx = valid_indices[np.argmax(prec[recall_mask])]
            best_threshold = thr[best_prec_idx] if best_prec_idx < len(
                thr) else 0.3
        else:
            # If we can't achieve min_recall, use a low threshold to maximize recall
            best_threshold = 0.3

        # Calculate metrics with best threshold
        predictions = (probs >= best_threshold).astype(int)

        fold_recall = recall_score(y_val, predictions)
        fold_precision = precision_score(y_val, predictions, zero_division=0)
        fold_f1 = 2 * (fold_precision * fold_recall) / \
            (fold_precision + fold_recall + 1e-8)

        fold_recalls.append(fold_recall)
        fold_precisions.append(fold_precision)
        fold_f1_scores.append(fold_f1)
        fold_thresholds.append(best_threshold)

        logger.info(f"Fold {fold} - Threshold: {best_threshold:.3f}, "
                    f"Precision: {fold_precision:.3f}, Recall: {fold_recall:.3f}, "
                    f"F1: {fold_f1:.3f}")

    # Calculate cross-validation statistics
    mean_recall = np.mean(fold_recalls)
    std_recall = np.std(fold_recalls)
    mean_precision = np.mean(fold_precisions)
    std_precision = np.std(fold_precisions)
    mean_f1 = np.mean(fold_f1_scores)
    std_f1 = np.std(fold_f1_scores)
    mean_threshold = np.mean(fold_thresholds)

    logger.info("\n" + "="*50)
    logger.info("K-FOLD CROSS-VALIDATION RESULTS")
    logger.info("="*50)
    logger.info(f"Recall:     {mean_recall:.3f} ± {std_recall:.3f}")
    logger.info(f"Precision:  {mean_precision:.3f} ± {std_precision:.3f}")
    logger.info(f"F1 Score:   {mean_f1:.3f} ± {std_f1:.3f}")
    logger.info(f"Avg Threshold: {mean_threshold:.3f}")
    logger.info("="*50)

    # Train final model on all data
    logger.info("Training final model on all data...")
    class_weights = {0: 1.0, 1: 3.0}
    final_clf = LogisticRegression(
        max_iter=2000, class_weight=class_weights, n_jobs=-1, random_state=42)
    final_clf.fit(X, y)

    # Use average threshold from k-fold
    final_threshold = mean_threshold

    # Save model
    model_path = training_dir / "classifier.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': final_clf,
            'threshold': final_threshold,
            'kfold_stats': {
                'mean_recall': mean_recall,
                'std_recall': std_recall,
                'mean_precision': mean_precision,
                'std_precision': std_precision,
                'mean_f1': mean_f1,
                'std_f1': std_f1,
                'k_folds': k_folds
            }
        }, f)

    logger.info(f"Final model saved to {model_path}")

    return final_clf, final_threshold, {
        'mean_recall': mean_recall,
        'std_recall': std_recall,
        'mean_precision': mean_precision,
        'std_precision': std_precision,
        'mean_f1': mean_f1,
        'std_f1': std_f1,

    }


def main():
    """
    Main function - choose what to do.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Simple importance classifier')
    parser.add_argument('--create', action='store_true',
                        help='Create training files')
    parser.add_argument('--update-labels', action='store_true',
                        help='Update labels from CSV')
    parser.add_argument('--train', action='store_true',
                        help='Train classifier')
    parser.add_argument('--kfold', action='store_true',
                        help='Train classifier with k-fold cross-validation')

    args = parser.parse_args()

    if args.create:
        create_training_files()
        print("Training files created! Please label the data in labels_to_fill.csv")

    elif args.update_labels:
        load_and_use_csv_labels()
        print("Labels updated from CSV")

    elif args.train:
        result = train_classifier()
        if result is not None:
            clf, threshold = result
            print(f"Training completed! Best threshold: {threshold:.3f}")
        else:
            print("Training failed - check your labels")

    elif args.kfold:
        result = train_classifier_with_kfold()
        if result is not None:
            clf, threshold, stats = result
            print(f"K-fold training completed!")
            print(
                f"Average recall: {stats['mean_recall']:.3f} ± {stats['std_recall']:.3f}")
            print(
                f"Average precision: {stats['mean_precision']:.3f} ± {stats['std_precision']:.3f}")
            print(f"Best threshold: {threshold:.3f}")
        else:
            print("K-fold training failed - check your labels")

    else:
        print("Choose an action:")
        print("--create: Create training files")
        print("--update-labels: Update labels from CSV")
        print("--train: Train classifier")
        print("--kfold: Train classifier with k-fold cross-validation")


if __name__ == "__main__":
    main()
