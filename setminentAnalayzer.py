from googletrans import Translator
from textblob import TextBlob
import json
import os
from typing import Dict, List, Tuple, Optional


class SentimentAnalyzer:
    """
    A sentiment analysis class that uses Google Translate and TextBlob
    to analyze sentiment of Hebrew text by translating it to English first.
    """

    def __init__(self):
        self.translator = Translator()
        self.source_language = 'he'
        self.target_language = 'en'

    def translate_with_googletrans(self, text: str) -> str:
        try:
            result = self.translator.translate(
                text, src=self.source_language, dest=self.target_language)
            return result.text
        except Exception as e:
            print(f"Error translating with Google Translate: {e}")
            return text

    def analyze_sentiment_textblob(self, text: str):

        try:
            blob = TextBlob(text)
            return blob
        except Exception as e:
            print(f"Error analyzing sentiment with TextBlob: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0}

    def analyze_utterances_file(self, file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                committie = json.load(f)

            results = []
            for mk in committie["utterances"].values():
                for utterance in mk['utterances']:
                    en_txt = self.translate_with_googletrans(
                        utterance)
                    sentiment = self.analyze_sentiment_textblob(en_txt)
                    results.append(sentiment)

            return results
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return []

    def batch_analyze_directory(self, directory_path: str) -> Dict[str, List[Dict]]:
        results = {}

        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                print(f"Analyzing {filename}...")
                results[filename] = self.analyze_utterances_file(
                    file_path)

        return results

    def save_results(self, results: Dict, output_path: str):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")


def analyze_sentiment():
    """
    Main function to demonstrate the sentiment analyzer functionality.
    """
    analyzer = SentimentAnalyzer()
    utterances_dir = "utterances"
    if os.path.exists(utterances_dir):
        print(f"\n=== Analyzing utterances directory: {utterances_dir} ===")
        results = analyzer.batch_analyze_directory(
            utterances_dir)
        analyzer.save_results(results, "sentiment_analysis_results.json")


if __name__ == "__main__":
    analyze_sentiment()
