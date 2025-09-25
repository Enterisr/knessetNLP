"""
Training script for importance classification using labeled data.
Creates a CSV file for manual labeling and trains a logistic regression classifier.
"""

import numpy as np
import pandas as pd
import pickle
import re
import json
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_curve, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from utils.logger_config import get_logger

logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


class ImportanceTrainer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.clf = None
        self.labels_file = PROJECT_ROOT / "training" / "importance_labels.csv"
        self.embeddings_file = PROJECT_ROOT / "utterance_embeddings.npy"
        self.data_file = PROJECT_ROOT / "utterances_data.pkl"

        # Create training directory if it doesn't exist
        (PROJECT_ROOT / "training").mkdir(exist_ok=True)

    def create_sample_labels_file(self, n_samples=500):
        """
        Create a CSV file with sample utterances for manual labeling.
        """
        logger.info("Creating sample labels file for manual annotation...")

        # Load existing data
        try:
            data = pd.read_pickle(self.data_file)
            logger.info(f"Loaded {len(data)} utterances from data file")
        except FileNotFoundError:
            logger.error(
                "Utterances data file not found. Run embedding first.")
            return

        # Sample diverse utterances (mix of short, medium, long)
        # Also try to get variety from different committees and speakers
        sample_data = []

        # Get short utterances (potential procedural)
        short_utters = data[data['text'].str.len() < 50].sample(
            min(100, len(data[data['text'].str.len() < 50])))
        sample_data.append(short_utters)

        # Get medium utterances
        medium_utters = data[(data['text'].str.len() >= 50) & (data['text'].str.len() < 200)].sample(
            min(200, len(data[(data['text'].str.len() >= 50) & (data['text'].str.len() < 200)])))
        sample_data.append(medium_utters)

        # Get long utterances (likely important)
        long_utters = data[data['text'].str.len() >= 200].sample(
            min(200, len(data[data['text'].str.len() >= 200])))
        sample_data.append(long_utters)

        # Combine all samples
        sample_df = pd.concat(sample_data).reset_index()

        # Create labels CSV
        labels_df = pd.DataFrame({
            'index': sample_df.index,
            # Reverse Hebrew text for better readability
            'text': sample_df['text'].str[::-1],
            'mk': sample_df['mk'].str[::-1] if 'mk' in sample_df.columns else '',
            'committee': sample_df.get('committee', ''),
            'important': '',  # Empty column for manual labeling
            'notes': ''  # Optional notes column
        })

        # Save to CSV
        labels_df.to_csv(self.labels_file, index=False, encoding='utf-8')
        logger.info(
            f"Created labels file with {len(labels_df)} samples: {self.labels_file}")
        logger.info(
            "Please fill the 'important' column with 1 (important) or 0 (not important)")

        return str(self.labels_file)

    def load_labeled_data(self):
        """
        Load the manually labeled data and prepare for training.
        """
        if not self.labels_file.exists():
            logger.error(
                "Labels file not found. Create it first using create_sample_labels_file()")
            return None, None, None

        # Load labels
        labels_df = pd.read_csv(self.labels_file, encoding='utf-8')

        # Filter out unlabeled rows
        labeled_df = labels_df[labels_df['important'].notna() & (
            labels_df['important'] != '')]

        if len(labeled_df) == 0:
            logger.error(
                "No labeled data found. Please fill the 'important' column in the CSV file.")
            return None, None, None

        logger.info(f"Found {len(labeled_df)} labeled examples")

        # Load embeddings and original data
        embeddings = np.load(self.embeddings_file)
        data = pd.read_pickle(self.data_file)

        # Get indices and extract corresponding embeddings
        indices = labeled_df['index'].values
        X_emb = embeddings[indices]

        # Get texts for handcrafted features
        texts = [data.iloc[i]['text'] for i in indices]

        # Convert labels to integers
        y = labeled_df['important'].astype(int).values

        logger.info(f"Label distribution: {np.bincount(y)}")

        return X_emb, texts, y

    def make_handcrafted_features(self, texts):
        """
        Create handcrafted features from text.
        """
        logger.info("Creating handcrafted features...")
        feats = []

        for text in texts:
            text = text or ""

            # Numeric content
            has_num = int(bool(re.search(r"\d", text)))

            # Money/budget related
            has_money = int(("₪" in text) or bool(
                re.search(r"\b(אלפים|מיליונ|תקציב|כסף|שקלים|מיליארד)\b", text)))

            # Procedural language
            procedural = int(bool(re.search(
                r"\b(תודה|מי בעד|מי נגד|נמשיך מחר|הישיבה נעולה|הצבעה|אושר|נדחה)\b", text)))

            # Questions (likely important)
            has_question = int("?" in text)

            # Length features
            text_length = len(text)
            word_count = len(text.split())

            # Emotional language
            has_strong_words = int(
                bool(re.search(r"\b(חמור|דחוף|חשוב|בעיה|משבר|מסוכן)\b", text)))

            # Policy/law related
            has_policy = int(
                bool(re.search(r"\b(חוק|הצעת|תקנה|חקיקה|מדיניות)\b", text)))

            feats.append([
                has_num, has_money, procedural, has_question,
                text_length, word_count, has_strong_words, has_policy
            ])

        return np.array(feats, dtype=np.float32)

    def train_classifier(self, test_size=0.2, threshold=0.8):
        """
        Train the logistic regression classifier.
        """
        logger.info("Loading labeled data...")
        X_emb, texts, y = self.load_labeled_data()

        if X_emb is None:
            return None

        # Create handcrafted features
        X_feats = self.make_handcrafted_features(texts)

        # Combine embeddings with handcrafted features
        X = np.hstack([X_emb, X_feats])
        logger.info(f"Feature matrix shape: {X.shape}")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_tr, X_va, y_tr, y_va = train_test_split(
            X_scaled, y, test_size=test_size, stratify=y, random_state=42
        )

        logger.info(f"Training set: {X_tr.shape[0]} samples")
        logger.info(f"Validation set: {X_va.shape[0]} samples")

        # Train classifier
        logger.info("Training logistic regression classifier...")
        self.clf = LogisticRegression(
            max_iter=2000,
            class_weight='balanced',
            n_jobs=-1,
            random_state=42
        )
        self.clf.fit(X_tr, y_tr)

        # Evaluate
        probs = self.clf.predict_proba(X_va)[:, 1]
        predictions = (probs >= threshold).astype(int)

        logger.info(f"\nClassification Report (threshold={threshold}):")
        print(classification_report(y_va, predictions, digits=3))

        # Additional metrics
        accuracy = accuracy_score(y_va, predictions)
        f1 = f1_score(y_va, predictions)

        logger.info(f"Accuracy: {accuracy:.3f}")
        logger.info(f"F1 Score: {f1:.3f}")

        # Precision-Recall curve analysis
        self.analyze_threshold(y_va, probs)

        # Save model
        self.save_model()

        return self.clf

    def analyze_threshold(self, y_true, probs):
        """
        Analyze different thresholds using precision-recall curve.
        """
        prec, rec, thresholds = precision_recall_curve(y_true, probs)

        # Find best threshold (balanced F1)
        f1_scores = 2 * (prec * rec) / (prec + rec + 1e-8)
        best_idx = np.argmax(f1_scores)
        best_threshold = thresholds[best_idx] if best_idx < len(
            thresholds) else 0.5

        logger.info(f"Best threshold for F1: {best_threshold:.3f}")
        logger.info(f"Best F1 score: {f1_scores[best_idx]:.3f}")

        # Plot PR curve
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 2, 1)
        plt.plot(rec, prec, 'b-', label='PR Curve')
        plt.plot(rec[best_idx], prec[best_idx], 'ro',
                 label=f'Best F1 @ {best_threshold:.2f}')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend()
        plt.grid(True)

        # Plot threshold vs F1
        plt.subplot(1, 2, 2)
        plt.plot(thresholds, f1_scores[:-1], 'g-', label='F1 Score')
        plt.axvline(best_threshold, color='r', linestyle='--',
                    label=f'Best: {best_threshold:.2f}')
        plt.xlabel('Threshold')
        plt.ylabel('F1 Score')
        plt.title('F1 Score vs Threshold')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(PROJECT_ROOT / "training" /
                    "threshold_analysis.png", dpi=300, bbox_inches='tight')
        plt.show()

        return best_threshold

    def predict_importance(self, texts=None, embeddings=None):
        """
        Predict importance for new texts.
        """
        if self.clf is None:
            logger.error(
                "Model not trained. Train first using train_classifier()")
            return None

        if embeddings is None:
            # If no embeddings provided, we need to embed the texts
            # This would require the embedding model
            logger.error("Embeddings required for prediction")
            return None

        # Create handcrafted features
        X_feats = self.make_handcrafted_features(texts)

        # Combine features
        X = np.hstack([embeddings, X_feats])
        X_scaled = self.scaler.transform(X)

        # Predict probabilities
        probs = self.clf.predict_proba(X_scaled)[:, 1]

        return probs

    def save_model(self):
        """
        Save the trained model and scaler.
        """
        model_path = PROJECT_ROOT / "training" / "importance_classifier.pkl"
        scaler_path = PROJECT_ROOT / "training" / "feature_scaler.pkl"

        with open(model_path, 'wb') as f:
            pickle.dump(self.clf, f)

        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

        logger.info(f"Model saved to {model_path}")
        logger.info(f"Scaler saved to {scaler_path}")

    def load_model(self):
        """
        Load a previously trained model.
        """
        model_path = PROJECT_ROOT / "training" / "importance_classifier.pkl"
        scaler_path = PROJECT_ROOT / "training" / "feature_scaler.pkl"

        try:
            with open(model_path, 'rb') as f:
                self.clf = pickle.load(f)

            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            logger.info("Model and scaler loaded successfully")
            return True
        except FileNotFoundError:
            logger.error("Model files not found")
            return False


def main():
    """
    Main function to run the training pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Train importance classifier')
    parser.add_argument('--create-labels', action='store_true',
                        help='Create sample labels CSV file')
    parser.add_argument('--train', action='store_true',
                        help='Train the classifier')
    parser.add_argument('--samples', type=int, default=500,
                        help='Number of samples for labeling')
    parser.add_argument('--threshold', type=float, default=0.8,
                        help='Classification threshold')

    args = parser.parse_args()

    trainer = ImportanceTrainer()

    if args.create_labels:
        labels_file = trainer.create_sample_labels_file(args.samples)
        print(f"Labels file created: {labels_file}")
        print("Please manually label the 'important' column with 1 (important) or 0 (not important)")
        print("Then run with --train flag to train the classifier")

    elif args.train:
        model = trainer.train_classifier(threshold=args.threshold)
        if model:
            print("Training completed successfully!")

    else:
        print("Use --create-labels to create labeling file or --train to train classifier")


if __name__ == "__main__":
    main()
