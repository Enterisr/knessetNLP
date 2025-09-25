import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import AutoModelForSequenceClassification, TextClassificationPipeline, AutoTokenizer

from translation.heb_to_eng_translator import HebToEngTranslator
from utils.logger_config import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    def __init__(self):
        # self.translator = HebToEngTranslator()
        model_name = "classla/xlm-r-parlasent"
        sentiment_tokenizer = AutoTokenizer.from_pretrained(model_name)
        sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            model_name)
        pipe = TextClassificationPipeline(model=sentiment_model, tokenizer=sentiment_tokenizer, return_all_scores=True,
                                          task='sentiment_analysis', device=0, function_to_apply="none")
        self.analyze = pipe

    def analyze_sentiment_model(self, text: str) -> float:
        try:
            results = self.analyze(text)
            return results[0][0]["score"]
        except Exception as e:
            logger.error("Error analyzing sentiment with model: %s", str(e))
            return 3

    def load_jsonl_data(self, jsonl_path: str):
        speakers_data = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if 'speaker_key' in data and 'utterances' in data:
                        speakers_data.append({
                            'speaker_name': data['speaker_key'],
                            'utterances': data['utterances']
                        })
                except json.JSONDecodeError:
                    continue
        return speakers_data

    def sample_utterances(self, utterances, max_utterances):
        if max_utterances is None or len(utterances) <= max_utterances:
            return utterances
        return random.sample(utterances, max_utterances)

    def analyze_speaker_sentiment(self, utterances):
        all_sentiments = 0
        processed_count = 0

        for utterance in utterances:
            try:
                #  en_txt = self.translator.translate(utterance)
                sentiment = self.analyze_sentiment_model(utterance)
                all_sentiments += sentiment
                processed_count += 1
                logger.info(
                    "Processed utterance with sentiment: %s, sentence is %s", sentiment, utterance[::-1])
            except (ValueError, TypeError) as e:
                logger.warning("Error processing utterance: %s", str(e))
                continue

        if processed_count > 0:
            return all_sentiments/processed_count
        return 3

    def find_matching_mk(self, speaker_name, mks_data):
        for mk_id, mk_info in mks_data.items():
            if 'FirstName' in mk_info and 'LastName' in mk_info:
                full_name = f"{mk_info['FirstName']} {mk_info['LastName']}"
                if speaker_name in full_name or full_name in speaker_name:
                    return mk_id
        return None

    def process_single_speaker(self, speaker_data, mks_data, max_utterances_per_mk, force_refresh):
        speaker_name = speaker_data['speaker_name']
        utterances = speaker_data['utterances']

        mk_id = self.find_matching_mk(speaker_name, mks_data)
        if not mk_id:
            return None

        # Check if sentiment already exists and force_refresh is False
        if not force_refresh and 'sentiment' in mks_data[mk_id]:
            logger.debug(
                "Sentiment already exists for MK %s (%s), skipping", mk_id, speaker_name)
            return None

        sampled_utterances = self.sample_utterances(
            utterances, max_utterances_per_mk)

        logger.info("Analyzing %d utterances for %s",
                    len(sampled_utterances), speaker_name)

        avg_sentiment = self.analyze_speaker_sentiment(sampled_utterances)

        return mk_id, speaker_name, avg_sentiment

    def analyze_jsonl_sentiment(self, jsonl_path: str, mks_data_path: str, max_utterances_per_mk=200, force_refresh=False):
        logger.info("Starting sentiment analysis with max %s utterances per MK (force_refresh=%s)",
                    max_utterances_per_mk or 'all', force_refresh)

        try:
            with open(mks_data_path, 'r', encoding='utf-8') as f:
                mks_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("Could not load %s: %s", mks_data_path, str(e))
            return

        speakers_data = self.load_jsonl_data(jsonl_path)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for speaker_data in speakers_data:
                future = executor.submit(self.process_single_speaker,
                                         speaker_data, mks_data, max_utterances_per_mk, force_refresh)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        mk_id, speaker_name, avg_sentiment = result
                        mks_data[mk_id]['sentiment'] = avg_sentiment
                        logger.info("Updated sentiment for MK %s (%s): %s",
                                    mk_id, speaker_name, avg_sentiment)
                except (ValueError, TypeError, KeyError) as e:
                    logger.error("Thread raised exception: %s", str(e))

        with open(mks_data_path, 'w', encoding='utf-8') as f:
            json.dump(mks_data, f, ensure_ascii=False, indent=2)

        logger.info("Sentiment analysis complete and saved to mks_data.json")


def analyze_sentiment(force_refresh=False):
    analyzer = SentimentAnalyzer()
    jsonl_path = "mk_utterances.jsonl"
    mks_data_path = "mks_data.json"

    if os.path.exists(jsonl_path) and os.path.exists(mks_data_path):
        analyzer.analyze_jsonl_sentiment(
            jsonl_path, mks_data_path, max_utterances_per_mk=500, force_refresh=force_refresh)
    else:
        logger.error("Required files not found")


if __name__ == "__main__":
    analyze_sentiment()
