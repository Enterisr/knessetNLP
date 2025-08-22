from setminent_analayzer import analyze_sentiment
from UtterancesExtraction.utterance_extractor import process_protocols
from data_fetcher import process_knesset_data
from embedder import embed
import argparse

OUTPUT_FOLDER = "committee_data"


def main():
    knesset_number = 25
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-refresh", dest="force_refresh",
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    # Step 1: Fetch and process Knesset data
    # This will also save the MKs data to mks_data.json
    # process_knesset_data(knesset=knesset_number,
    #                     force_refresh = args.force_refresh)

    # Step 2: Process protocols to extract utterances and enrich with MKs data
    process_protocols(OUTPUT_FOLDER, force_refresh=True)

    # Step 3: Process Agressiveness
  #  analyze_sentiment(force_refresh=args.force_refresh)
   # embed(force_refresh=args.force_refresh)


if __name__ == "__main__":
    main()
