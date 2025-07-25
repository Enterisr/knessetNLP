import re
import os
import json


def extract_utterance_from_file(content: str):

    speaker_utterances = {}

    pattern = r'<< דובר >>\s*(?P<speaker>[^:]+):\s*<< דובר >>\s*(?P<utterance>[^<]+)'
    matches = re.finditer(pattern, content)

    for match in matches:
        speaker = match.group('speaker').strip()
        utterance = match.group('utterance').strip()

        if speaker and utterance:
            if speaker not in speaker_utterances:
                speaker_utterances[speaker] = []
            speaker_utterances[speaker].append(utterance)

    return speaker_utterances


def process_protocols(output_folder="committee_data"):
    """
    Process all JSON files in the output folder to extract utterances by speaker.
    """
    for file_name in os.listdir(output_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(output_folder, file_name)

            with open(file_path, "r", encoding="utf-8") as f:
                protocol_data = json.load(f)
                utterances = extract_utterance_from_file(protocol_data["text"])
                # Save the utterances back into the JSON file
                protocol_data["utterances"] = utterances

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(protocol_data, f,
                              ensure_ascii=False, indent=2)
