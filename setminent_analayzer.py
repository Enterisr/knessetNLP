from textblob import TextBlob
import json
import os
from typing import Dict

from heb_to_eng_translator import HebToEngTranslator


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
            print(f"Error analyzing sentiment with TextBlob: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0}

    def analyze_utterances_file(self, file_path: str) -> bool:
        with open(file_path, 'r', encoding='utf-8') as f:
            committee = json.load(f)

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

            print(
                f"Finished Analyzing mk: {key_mk} with polarity: {total_sentiment['polarity']} with subjectivity: {total_sentiment['subjectivity']}")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(committee, f, ensure_ascii=False, indent=2)

        print(f"Sentiment analysis saved to {file_path}")
        return True

    def batch_analyze_directory(self, directory_path: str) -> Dict[str, bool]:
        results = {}

        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                print(f"Analyzing {filename}...")
                results[filename] = self.analyze_utterances_file(file_path)

        return results


def analyze_sentiment():
    """
    Main function to demonstrate the sentiment analyzer functionality.
    """
    analyzer = SentimentAnalyzer()
    utterances_dir = "utterances"
    if os.path.exists(utterances_dir):
        print(f"\n=== Analyzing utterances directory: {utterances_dir} ===")
        results = analyzer.batch_analyze_directory(utterances_dir)

        # Print summary of results
        successful = sum(results.values())
        total = len(results)
        print(f"Successfully processed: {successful}/{total} files")
        if successful < total:
            failed_files = [filename for filename,
                            success in results.items() if not success]
            print(f"Failed files: {failed_files}")


if __name__ == "__main__":
    analyze_sentiment()
