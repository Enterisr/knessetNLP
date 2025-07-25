import re
import os
import json


def load_mks_data(file_path="mks_data.json"):
    """
    Load MKs data from a JSON file.

    Args:
        file_path (str): Path to the JSON file with MKs data

    Returns:
        dict: Dictionary containing MKs data or empty dict if file not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"MKs data file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding MKs data file: {file_path}")
        return {}


def extract_utterance_from_file(file: str, mks_data=None):
    """
    Extracts utterances from a given text file and groups them by speaker.
    Also enriches speaker information if MKs data is provided.

    Args:
        file (str): Path to the text file.
        mks_data (dict, optional): Dictionary containing MKs data for enriching speaker info.

    Returns:
        dict: A dictionary where keys are speaker names and values are lists of their utterances.
    """
    speaker_utterances = {}

    # Load MKs data if not provided
    if mks_data is None:
        mks_data = load_mks_data()

    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'<< דובר >>\s*(?P<speaker>[^:]+):\s*<< דובר >>\s*(?P<utterance>[^<]+)'
        matches = re.finditer(pattern, content)

        for match in matches:
            speaker = match.group('speaker').strip()
            utterance = match.group('utterance').strip()

            # Extract MK information if possible
            speaker_info = {
                "name": speaker,
                "utterance": utterance
            }

            # Try to match with MK data
            mk_matched = False
            for mk_id, mk_info in mks_data.items():
                full_name = f"{mk_info['FirstName']} {mk_info['LastName']}"
                if full_name in speaker or speaker in full_name:
                    speaker_info["mk_id"] = mk_id
                    speaker_info["faction"] = mk_info.get("FactionName", "")
                    mk_matched = True
                    break

            if speaker and utterance:
                if speaker not in speaker_utterances:
                    speaker_utterances[speaker] = {
                        "utterances": [],
                        "mk_info": mk_matched
                    }
                speaker_utterances[speaker]["utterances"].append(speaker_info)

        # Handle interjections (<< קריאה >>)
        interjection_pattern = r'<< קריאה >>\s*(?P<interjection>[^<]+)'
        interjections = re.findall(interjection_pattern, content)
        if interjections:
            speaker_utterances['Interjections'] = [i.strip()
                                                   for i in interjections]

    except FileNotFoundError:
        print(f"File not found: {file}")
    except IOError as e:
        print(f"I/O error while processing file {file}: {e}")

    return speaker_utterances


def process_protocols(output_folder="committee_data"):
    """
    Process all JSON files in the output folder to extract utterances by speaker.
    Uses MKs data to enrich speaker information when possible.
    """
    # Load MKs data once for all files
    mks_data = load_mks_data()

    for file_name in os.listdir(output_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(output_folder, file_name)

            with open(file_path, "r", encoding="utf-8") as f:
                protocol_data = json.load(f)

            source_file = protocol_data.get("source_file")
            if source_file:
                # Download and convert the source file to text
                local_path = os.path.join(
                    "temp", os.path.basename(source_file))
                if os.path.exists(local_path):
                    # Process utterances with MKs data
                    utterances = extract_utterance_from_file(
                        local_path, mks_data)

                    # Save the utterances back into the JSON file
                    protocol_data["utterances"] = utterances

                    # Add statistics about MKs participation
                    mk_stats = {}
                    for _, data in utterances.items():
                        if isinstance(data, dict) and data.get("mk_info"):
                            # Count utterances by faction
                            for utterance in data["utterances"]:
                                if "faction" in utterance:
                                    faction = utterance["faction"]
                                    if faction not in mk_stats:
                                        mk_stats[faction] = 0
                                    mk_stats[faction] += 1

                    # Add statistics to the protocol data
                    protocol_data["mk_stats"] = mk_stats

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(protocol_data, f,
                                  ensure_ascii=False, indent=2)
