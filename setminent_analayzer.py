from concurrent.futures import ThreadPoolExecutor, as_completed
from textblob import TextBlob
import json
import os

from heb_to_eng_translator import HebToEngTranslator
from logger_config import get_logger

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
            return blob
        except Exception as e:
            logger.error(f"Error analyzing sentiment with TextBlob: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0}

    def analyze_utterances_file(self, file_path: str, force_reload: bool) -> bool:
        with open(file_path, 'r', encoding='utf-8') as f:
            committee = json.load(f)
            if len(committee["utterances"].values()) > 0:
                sentiment_exists = list(committee["utterances"].values())[
                    0].get("sentiment")
                if sentiment_exists is not None and not force_reload:
                    logger.debug(
                        f"sentiment already exists in {file_path}, not updating")
                    return True

                for key_mk, mk_data in committee["utterances"].items():
                    acc_sentiment = {"subjectivity": 0, "polarity": 0}
                    for utterance in mk_data['utterances']:
                        en_txt = self.translator.translate(utterance)
                        sentiment = self.analyze_sentiment_textblob(en_txt)
                        acc_sentiment["polarity"] += sentiment.polarity
                        acc_sentiment["subjectivity"] += sentiment.subjectivity

                    total_sentiment = {
                        "polarity": acc_sentiment["polarity"] / len(mk_data['utterances']),
                        "subjectivity": acc_sentiment["subjectivity"] / len(mk_data['utterances'])
                    }

                    mk_data["sentiment"] = total_sentiment

                    logger.ifno(
                        f"Finished Analyzing mk: {key_mk} with polarity: {total_sentiment['polarity']} with subjectivity: {total_sentiment['subjectivity']}")

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(committee, f, ensure_ascii=False, indent=2)

                logger.info(f"Sentiment analysis saved to {file_path}")
                return True

    def batch_analyze_directory(self, directory_path: str, force_refresh: bool):

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for filename in os.listdir(directory_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(directory_path, filename)
                    print(f"Analyzing {filename}...")
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
    analyze_sentiment()
