from sentiment.sentiment_analyzer import analyze_sentiment
from UtterancesExtraction.utterance_extractor import process_protocols
from DataFetching.data_fetcher import KnessetDataFetcher
from DataFetching.photo_enricher import enrich_photos
from processing.embedder import embed
import argparse
from utils.logger_config import get_logger
from processing import init_repo_server, run_tf_idf_analysis
logger = get_logger(__name__)
OUTPUT_FOLDER = "committee_data"


def full_pipeline(args):
    knesset_number = 25

    # Step 1: Fetch and process Knesset data
    # This will also save the MKs data to mks_data.json
    # logger.info(f"started process_knesset_data with knesset {knesset_number}")
    fetcher = KnessetDataFetcher(
        knesset_num=knesset_number, force_refresh=args.force_refresh)
    fetcher.process_knesset_data()

    # Step 1.5: Enrich MKs data with photos
    logger.info("Starting photo enrichment of MKs data...")
    enrich_photos(force_refresh=args.force_refresh)

    # Step 2: Process protocols to extract utterances and enrich with MKs data
    logger.info(
        f"started process_protocols to utterances with knesset {knesset_number}")
    process_protocols(
        OUTPUT_FOLDER, force_refresh=args.force_refresh)

    #  Step 3: Process Agressiveness
    logger.info(f"started analyzing santiment of utterances")
    analyze_sentiment(force_refresh=args.force_refresh)
    logger.info(f"started embedding utterances")
    embed(force_refresh=args.force_refresh)


def init_repo(args):
    init_repo_server(args.force_refresh)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-refresh", dest="force_refresh",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-txt",
                        dest="save_txt",
                        action=argparse.BooleanOptionalAction,
                        help="Save TXT files during processing")
    parser.add_argument("--only-search",
                        dest="only_search",
                        action=argparse.BooleanOptionalAction,
                        help="Run only for server queries, dont run full pipeline (Assume its already there)")
    parser.add_argument("--serve",
                        dest="only_search",
                        action=argparse.BooleanOptionalAction,
                        help="Alias for --only-search: Run only for server queries, dont run full pipeline (Assume its already there)")

    args = parser.parse_args()

    if args.force_refresh:
        logger.info("Forcing refresh of all data...")
    if args.only_search:
        init_repo(args)
    else:
        full_pipeline(args)


if __name__ == "__main__":
    # run_tf_idf_analysis()
    # embed()
    run()
