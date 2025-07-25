import os
from utterance import process_protocols
from data_fetcher import process_knesset_data

OUTPUT_FOLDER = "committee_data"


def main():
    knesset_number = 25

    # Step 1: Fetch and process Knesset data
    # This will also save the MKs data to mks_data.json
    process_knesset_data(knesset_number)

    # Step 2: Process protocols to extract utterances and enrich with MKs data
    process_protocols(OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
