import re
import os
import json

from UtterancesExtraction.dover_resolver import DoverResolver
from logger_config import get_logger

logger = get_logger(__name__)


def extract_pretext_info(dover_resolver: DoverResolver, text: str) -> tuple:
    mks_from_list = set()
    chairs = set()
    topic = ""
    topic_match = re.search(
        r"<< נושא >>\s*(?P<topic>[^<]+?)\s*<< נושא >>", text)
    if topic_match:
        topic = topic_match.group("topic").strip()

    chair_matches = re.findall(
        r"(?P<name>.+?)\s+[–-]\s+(?P<role>יו\"ר|מ\"מ היו\"ר)", text)
    for name, _ in chair_matches:
        mks_from_list.add(
            dover_resolver.extract_name_key_from_dover(name.strip()))
        chairs.add(name.strip())

    # Extract both sections and combine their lines
    combined_lines = []
    for section_title in ["חברי הוועדה", "חברי הכנסת"]:
        section_match = re.search(
            rf"{section_title}:\s*\n(?P<section>.*?)(?:\n\s*\n|מוזמנים:|חברי הוועדה:|חברי הכנסת:)", text, re.S)
        if section_match:
            lines = section_match.group("section").splitlines()
            combined_lines.extend([line.strip()
                                  for line in lines if line.strip()])

    for line in combined_lines:
        mks_from_list.add(dover_resolver.extract_name_key_from_dover(line))

    return mks_from_list, chairs, topic


def extract_utterance_from_file(dover_resolver: DoverResolver, content: str):

    mks_in_meeting, chairs, title = extract_pretext_info(dover_resolver,
                                                         content)
    speaker_utterances = {}
    pattern = r'<< (?:דובר|יור) >>\s*(?P<speaker>[^:]+):\s*<< (?:דובר|יור) >>\s*(?P<utterance>[^<]+)'

    matches = re.finditer(pattern, content)

    for match in matches:
        speaker = match.group('speaker').strip()
        utterance = match.group('utterance').strip()

        if speaker and utterance:
            if speaker not in speaker_utterances:
                speaker_key, mk_meta = dover_resolver.resolve_mk(
                    speaker, mks_in_meeting)
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
    dover_resolver = DoverResolver()
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
                        dover_resolver, protocol_data["text"])

                    del protocol_data["text"]
                    protocol_data["utterances"] = utterances

                    # Save utterances to separate file
                    with open(utterances_file_path, "w", encoding="utf-8") as f:
                        json.dump(protocol_data, f,
                                  ensure_ascii=False, indent=2)
