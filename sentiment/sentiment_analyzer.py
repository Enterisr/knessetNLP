from concurrent.futures import ThreadPoolExecutor, as_completed
from textblob import TextBlob
import json
import os
from pathlib import Path

from translation.heb_to_eng_translator import HebToEngTranslator
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

logger = get_logger(__name__)


class SentimentAnalyzer:
    """
    A sentiment analysis class that uses Google Translate and TextBlob
    to analyze sentiment of Hebrew text by translating it to English first.
    """

    def __init__(self):
        self.translator = HebToEngTranslator()

    def analyze_sentiment_textblob(self, text: str):
        try:
            blob = TextBlob(text)
            # Get sentiment values, handling any attribute access issues
            try:
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
            except (AttributeError, TypeError):
                # Fallback values if sentiment access fails
                polarity = 0.0
                subjectivity = 0.0

            return {
                'polarity': float(polarity),
                'subjectivity': float(subjectivity)
            }
        except (AttributeError, ValueError) as e:
            logger.error("Error analyzing sentiment with TextBlob: %s", str(e))
            return {'polarity': 0.0, 'subjectivity': 0.0}

    def analyze_utterances_file(self, file_path: str, force_reload: bool) -> bool:
        with open(file_path, 'r', encoding='utf-8') as f:
            committee = json.load(f)
            if len(committee["utterances"].values()) > 0:
                sentiment_exists = list(committee["utterances"].values())[
                    0].get("sentiment")
                if sentiment_exists is not None and not force_reload:
                    logger.debug(
                        "sentiment already exists in %s, not updating", file_path)
                    return True

                for key_mk, mk_data in committee["utterances"].items():
                    acc_sentiment = {"subjectivity": 0.0, "polarity": 0.0}
                    for utterance in mk_data['utterances']:
                        en_txt = self.translator.translate(utterance)
                        sentiment = self.analyze_sentiment_textblob(en_txt)
                        acc_sentiment["polarity"] += sentiment["polarity"]
                        acc_sentiment["subjectivity"] += sentiment["subjectivity"]

                    total_sentiment = {
                        "polarity": acc_sentiment["polarity"] / len(mk_data['utterances']),
                        "subjectivity": acc_sentiment["subjectivity"] / len(mk_data['utterances'])
                    }

                    mk_data["sentiment"] = total_sentiment

                    logger.info("Finished Analyzing mk: %s with polarity: %s with subjectivity: %s",
                                key_mk, total_sentiment['polarity'], total_sentiment['subjectivity'])

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(committee, f, ensure_ascii=False, indent=2)

                logger.info("Sentiment analysis saved to %s", file_path)
                return True
        return False

    def batch_analyze_directory(self, directory_path: str, force_refresh: bool):
        """
        Analyze sentiment for all utterance files in the directory.
        Requires partition folder system (part_0, part_1, etc.).
        """
        # Check for partition folders
        items_in_dir = os.listdir(directory_path)
        partition_folders = [
            item for item in items_in_dir
            if item.startswith("part_") and os.path.isdir(os.path.join(directory_path, item))
        ]

        if not partition_folders:
            raise ValueError(
                f"No partition folders found in {directory_path}. Expected folders named 'part_0', 'part_1', etc.")

        files_to_process = []

        # Process files from all partition folders
        logger.info("Found %d partition folders: %s", len(
            partition_folders), sorted(partition_folders))
        for partition_folder in sorted(partition_folders):
            partition_path = os.path.join(directory_path, partition_folder)
            for file_name in os.listdir(partition_path):
                if file_name.endswith('.json'):
                    full_path = os.path.join(partition_path, file_name)
                    files_to_process.append((file_name, full_path))

        logger.info("Processing %d utterance files for sentiment analysis from %d partitions",
                    len(files_to_process), len(partition_folders))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for file_name, file_path in files_to_process:
                print(f"Analyzing {file_name}...")
                futures.append(executor.submit(
                    self.analyze_utterances_file, file_path, force_refresh))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Thread raised exception: {e}")


def analyze_sentiment(force_refresh=False):
    """
    Main function to demonstrate the sentiment analyzer functionality.
    """
    analyzer = SentimentAnalyzer()
    utterances_dir = "utterances"
    if os.path.exists(utterances_dir):
        logger.info(
            f"\n=== Analyzing utterances directory: {utterances_dir} ===")
        analyzer.batch_analyze_directory(utterances_dir, force_refresh)


if __name__ == "__main__":
    analyze_sentiment(force_refresh=True)
