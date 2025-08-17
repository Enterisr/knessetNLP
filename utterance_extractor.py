import re
import os
import json


def load_mks_data():
    """
    Load and return the MK (Member of Knesset) data from a JSON file.
    """
    try:
        with open('mks_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: mks_data.json file not found. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        print("Warning: Error parsing mks_data.json. Returning empty dictionary.")
        return {}


def transfer_mks_to_name_format(mks: dict) -> dict:
    mks_by_name = {}
    for key in mks.keys():
        new_key = mks[key]["FirstName"]+" "+mks[key]["LastName"]
        mks_by_name[new_key] = mks[key]
    return mks_by_name


def extract_name_key_from_dover(dover_str: str) -> str:
    match = re.match(r"^(.*?) \(", dover_str)
    if match:
        name = match.group(1)
    else:
        parts = dover_str.split()
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""
        name = first+last
    print(f"mk key: {name}")
    return name


def extract_utterance_from_file(mks: dict, content: str):

    speaker_utterances = {}
    # add יור and other roles
    pattern = r'<< דובר >>\s*(?P<speaker>[^:]+):\s*<< דובר >>\s*(?P<utterance>[^<]+)'
    matches = re.finditer(pattern, content)

    for match in matches:
        speaker = match.group('speaker').strip()
        utterance = match.group('utterance').strip()

        if speaker and utterance:
            if speaker not in speaker_utterances:
                speaker_key = extract_name_key_from_dover(speaker)
                if not speaker_key == "קריאה":
                    mk_meta = mks.get(speaker_key, {})

                    if mk_meta is not None:
                        # first time speaking
                        if speaker_utterances.get(speaker_key) is None:
                            speaker_utterances[speaker_key] = {}
                            speaker_utterances[speaker_key]["utterances"] = []
                        speaker_utterances[speaker_key]["metadata"] = mk_meta
                        speaker_utterances[speaker_key]["utterances"].append(
                            utterance)

    return speaker_utterances


def process_protocols(output_folder="committee_data", utterances_folder="utterances", force_refresh=False):
    """
    Process all JSON files in the output folder to extract utterances by speaker.
    Save utterances to separate files in a dedicated utterances folder.
    """
    mks = load_mks_data()
    mks_by_name = transfer_mks_to_name_format(mks)

    # Create utterances folder if it doesn't exist
    os.makedirs(utterances_folder, exist_ok=True)

    for file_name in os.listdir(output_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(output_folder, file_name)

            with open(file_path, "r", encoding="utf-8") as f:
                # Create utterances file path
                utterances_file_name = f"utterances_{file_name}"
                utterances_file_path = os.path.join(
                    utterances_folder, utterances_file_name)
                if force_refresh or not os.path.exists(utterances_file_path):
                    protocol_data = json.load(f)
                    utterances = extract_utterance_from_file(
                        mks_by_name, protocol_data["text"])

                    del protocol_data["text"]
                    protocol_data["utterances"] = utterances

                    # Save utterances to separate file
                    with open(utterances_file_path, "w", encoding="utf-8") as f:
                        json.dump(protocol_data, f,
                                  ensure_ascii=False, indent=2)
