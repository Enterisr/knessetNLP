import re
import os
import json
from multiprocessing import Pool, cpu_count

from UtterancesExtraction.dover_resolver import DoverResolver
from logger_config import get_logger
MINIMAL_UTTERANCE_SIZE = 3
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

    mks_in_meeting, _, title = extract_pretext_info(dover_resolver,
                                                    content)
    speaker_utterances = {}
    pattern = r'<< (?:דובר|יור) >>\s*(?P<speaker>[^:]+):\s*<< (?:דובר|יור) >>\s*(?P<utterance>[^<]+)'

    matches = re.finditer(pattern, content)

    for match in matches:
        speaker = match.group('speaker').strip()
        utterance = match.group('utterance').strip()

        if speaker and utterance and len(utterance.split(" ")) >= MINIMAL_UTTERANCE_SIZE:
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

    return title, speaker_utterances


def _discover_partitions(output_folder: str) -> dict:
    """
    Discover all partitions and their files.

    Returns:
        Dict mapping partition names to list of (file_name, full_file_path) tuples
    """
    partitions = {}
    items_in_output = os.listdir(output_folder)
    partition_folders = [
        item for item in items_in_output
        if item.startswith("part_") and os.path.isdir(os.path.join(output_folder, item))
    ]

    if not partition_folders:
        raise ValueError(
            f"No partition folders found in {output_folder}. Expected folders named 'part_0', 'part_1', etc.")

    logger.info("Found %d partition folders: %s", len(
        partition_folders), sorted(partition_folders))

    for partition_folder in sorted(partition_folders):
        partition_path = os.path.join(output_folder, partition_folder)
        partition_files = []
        for file_name in os.listdir(partition_path):
            if file_name.endswith(".json"):
                full_path = os.path.join(partition_path, file_name)
                partition_files.append((file_name, full_path))

        if partition_files:  # Only add if there are files
            partitions[partition_folder] = partition_files

    return partitions


def _create_utterances_output_path(utterances_folder: str, partition_folder: str, file_name: str) -> str:
    """
    Create the output path for utterances file, maintaining partition structure.

    Args:
        utterances_folder: Base utterances folder
        partition_folder: Partition folder name (e.g., 'part_0', 'part_1')
        file_name: Original JSON file name

    Returns:
        Full path for the utterances output file
    """
    utterances_file_name = f"utterances_{file_name}"

    # Create partition folder in utterances directory
    utterances_partition_folder = os.path.join(
        utterances_folder, partition_folder)
    os.makedirs(utterances_partition_folder, exist_ok=True)
    return os.path.join(utterances_partition_folder, utterances_file_name)


def _process_single_protocol_file(dover_resolver: DoverResolver, file_path: str, output_path: str) -> None:
    """
    Process a single protocol JSON file to extract utterances.

    Args:
        dover_resolver: DoverResolver instance for MK name resolution
        file_path: Path to input JSON file
        output_path: Path where utterances file should be saved
    """
    with open(file_path, "r", encoding="utf-8") as f:
        protocol_data = json.load(f)

    title, utterances = extract_utterance_from_file(
        dover_resolver, protocol_data["text"])

    # Remove original text and add extracted data
    del protocol_data["text"]
    protocol_data["utterances"] = utterances
    protocol_data["subject"] = title

    # Save utterances to output file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(protocol_data, f, ensure_ascii=False, indent=2)


def _process_partition(partition_data: tuple) -> set:
    """
    Process all files in a single partition.

    Args:
        partition_data: Tuple of (partition_name, files_list, utterances_folder, force_refresh)

    Returns:
        Set of unmatched person keys from this partition
    """
    partition_name, files_list, utterances_folder, force_refresh = partition_data
    dover_resolver = DoverResolver()

    logger.info("Process starting for partition: %s (%d files)",
                partition_name, len(files_list))

    processed_count = 0
    for file_name, file_path in files_list:
        # Create output path
        utterances_file_path = _create_utterances_output_path(
            utterances_folder, partition_name, file_name)

        # Process file if needed
        if force_refresh or not os.path.exists(utterances_file_path):
            try:
                _process_single_protocol_file(
                    dover_resolver, file_path, utterances_file_path)
                processed_count += 1
            except (IOError, json.JSONDecodeError, KeyError) as e:
                logger.error("Error processing %s: %s", file_path, str(e))
        else:
            logger.debug("Skipping %s (already exists)", utterances_file_path)

    logger.info("Process completed for partition: %s (%d files processed)",
                partition_name, processed_count)

    return set(dover_resolver.no_match_person)


def _save_unmatched_keys(all_unmatched_keys: set, output_file: str = "not_found_keys.txt") -> None:
    """Save unmatched person keys to a file for debugging."""
    with open(output_file, "w", encoding="utf-8") as f:
        for key in sorted(all_unmatched_keys):
            f.write(f"{key}\n")


def process_protocols(output_folder="committee_data", utterances_folder="utterances",
                      force_refresh=True, max_processes=None):
    """
    Process all JSON files in the output folder to extract utterances by speaker.
    Save utterances to separate files in a dedicated utterances folder.
    Requires partition folder system (part_0, part_1, etc.).

    Uses multiprocessing to process each partition in parallel.

    Args:
        output_folder: Folder containing partition folders with protocol JSON files
        utterances_folder: Folder where utterances files will be saved
        force_refresh: Whether to reprocess existing files
        max_processes: Maximum number of processes to use (None = cpu_count)
    """
    os.makedirs(utterances_folder, exist_ok=True)

    partitions = _discover_partitions(output_folder)

    if not partitions:
        logger.warning("No JSON files found in %s", output_folder)
        return

    total_files = sum(len(files) for files in partitions.values())
    logger.info("Found %d partitions with %d total JSON files to process",
                len(partitions), total_files)

    if max_processes is None:
        max_processes = min(cpu_count(), len(partitions))

    logger.info("Using %d processes for %d partitions",
                max_processes, len(partitions))

    partition_data_list = [
        (partition_name, files_list, utterances_folder, force_refresh)
        for partition_name, files_list in partitions.items()
    ]

    all_unmatched_keys = set()

    with Pool(processes=max_processes) as pool:
        results = pool.map(_process_partition, partition_data_list)

        for unmatched_keys in results:
            all_unmatched_keys.update(unmatched_keys)

    logger.info("Processing complete. Found %d total unmatched keys",
                len(all_unmatched_keys))
    _save_unmatched_keys(all_unmatched_keys)


if __name__ == "__main__":
    # Example usage
    process_protocols()
