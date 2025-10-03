from processing.clusterer import Clusterer
from sentiment.sentiment_analyzer import analyze_sentiment
from UtterancesExtraction.utterance_extractor import process_protocols
from DataFetching.data_fetcher import KnessetDataFetcher
from DataFetching.photo_enricher import enrich_photos
from processing.embedder import embed
import argparse
from trash_utterances_detector.trainer import train_classifier_with_kfold
from utils.logger_config import get_logger
from processing import init_repo_server
logger = get_logger(__name__)
OUTPUT_FOLDER = "committee_data"


def init_repo(args):
    init_repo_server(args.force_refresh)


def full_pipeline(args):
    knesset_number = 25
    logger.info(f"started process_knesset_data with knesset {knesset_number}")
    fetcher = KnessetDataFetcher(
        knesset_num=knesset_number, force_refresh=args.force_refresh)
    fetcher.process_knesset_data()

    logger.info("Starting photo enrichment of MKs data...")
    enrich_photos(force_refresh=args.force_refresh)

    logger.info(
        f"started process_protocols to utterances with knesset {knesset_number}")
    process_protocols(
        OUTPUT_FOLDER, force_refresh=args.force_refresh)

    logger.info(f"started analyzing santiment of utterances")
    analyze_sentiment(force_refresh=args.force_refresh)
    embed(force_refresh=args.force_refresh)
    logger.info(f"started INIT REPO")
    init_repo(args)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-refresh", dest="force_refresh",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-txt",
                        dest="save_txt",
                        action=argparse.BooleanOptionalAction,
                        help="Save TXT files during processing")
    parser.add_argument("--complete",
                        dest="run_pipeline",
                        action=argparse.BooleanOptionalAction,
                        help="run full data pipeline (and not only init repo, which will allow the app to function)")
    parser.add_argument("--run-pipeline",
                        dest="run_pipeline",
                        action=argparse.BooleanOptionalAction,
                        help="Alias for --run-pipeline: run full pipeline")

    args = parser.parse_args()

    if args.force_refresh:
        logger.info("Forcing refresh of all data...")
    if args.run_pipeline:
        logger.info("Running full pipeline...")
        full_pipeline(args)
    else:
        logger.info("Running init repo...")
        init_repo(args)


if __name__ == "__main__":
    run()
