from setminent_analayzer import analyze_sentiment
from UtterancesExtraction.utterance_extractor import process_protocols
from data_fetcher import process_knesset_data
from embedder import embed
import argparse
from logger_config import get_logger

logger = get_logger(__name__)
OUTPUT_FOLDER = "committee_data"


def main():
    knesset_number = 25
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-refresh", dest="force_refresh",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--save-txt",
                        dest="save_txt",
                        action=argparse.BooleanOptionalAction,
                        help="Save TXT files during processing")
    args = parser.parse_args()

    if args.force_refresh:
        logger.info("Forcing refresh of all data...")

    # Step 1: Fetch and process Knesset data
    # This will also save the MKs data to mks_data.json
    logger.info(f"started process_knesset_data with knesset {knesset_number}")
    process_knesset_data(knesset=knesset_number,
                         force_refresh=args.force_refresh, to_save_txt=args.save_txt)

    # Step 2: Process protocols to extract utterances and enrich with MKs data
    logger.info(
        f"started process_protocols to utterances with knesset {knesset_number}")
    process_protocols(
        OUTPUT_FOLDER, force_refresh=args.force_refresh)

    # Step 3: Process Agressiveness
    logger.info(f"started analyzing santiment of utterances")
    analyze_sentiment(force_refresh=args.force_refresh)
    logger.info(f"started embedding utterances")
    embed(force_refresh=args.force_refresh)


if __name__ == "__main__":
    main()
