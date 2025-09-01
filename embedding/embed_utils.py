import os
from utils.logger_config import get_logger

logger = get_logger(__name__)


def get_utterances_files_list(directory: str) -> list[str]:

    partition_folders = _get_partition_folders(directory)
    logger.info("Found %d partition folders: %s", len(
        partition_folders), partition_folders)

    files_to_process = _get_files_to_process(partition_folders, directory)
    logger.info("Processing %d utterance files from %d partitions",
                len(files_to_process), len(partition_folders))
    return files_to_process


def _get_partition_folders(directory: str) -> list:
    items_in_dir = os.listdir(directory)
    partition_folders = [
        item for item in items_in_dir
        if item.startswith("part_") and os.path.isdir(os.path.join(directory, item))
    ]
    if not partition_folders:
        raise ValueError(
            f"No partition folders found in {directory}. Expected folders named 'part_0', 'part_1', etc.")
    return sorted(partition_folders)


def _get_files_to_process(partition_folders: list, directory: str) -> list:
    files_to_process = []
    for partition_folder in partition_folders:
        partition_path = os.path.join(directory, partition_folder)
        for file_name in os.listdir(partition_path):
            if file_name.endswith('.json'):
                full_path = os.path.join(partition_path, file_name)
                files_to_process.append((file_name, full_path))
    return files_to_process
