import os
import sys
from collections import defaultdict
from pathlib import Path
from utils.logger_config import get_logger


class DuplicateFileChecker:
    """
    A class for checking duplicate JSON files after data fetching.
    """

    def __init__(self, output_folder: str = "committee_data"):
        """
        Initialize the DuplicateFileChecker.

        Args:
            output_folder (str): The folder to check for duplicate files
        """
        self.output_folder = output_folder
        self.logger = get_logger(__name__)

    def check_for_duplicates(self) -> bool:
        """
        Check for duplicate JSON files in the output folder.

        Returns:
            bool: True if no duplicates found, False if duplicates detected
        """
        if not os.path.exists(self.output_folder):
            self.logger.warning(
                f"Output folder '{self.output_folder}' does not exist")
            return True

        duplicates = self._find_duplicate_files()

        if duplicates:
            self._log_and_exit_on_duplicates(duplicates)
            return False

        self.logger.info("No duplicate JSON files found")
        return True

    def _find_duplicate_files(self) -> dict:
        """
        Find duplicate JSON files by scanning the output folder recursively.

        Returns:
            dict: Dictionary with filenames as keys and lists of full paths as values
                 Only includes files that appear more than once
        """
        file_map = defaultdict(list)

        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.output_folder):
            for file in files:
                if file.endswith('.json'):
                    full_path = os.path.join(root, file)
                    file_map[file].append(full_path)

        # Filter to only include duplicates
        duplicates = {filename: paths for filename,
                      paths in file_map.items() if len(paths) > 1}

        return duplicates

    def _log_and_exit_on_duplicates(self, duplicates: dict) -> None:
        """
        Log error messages for duplicate files and exit the program.

        Args:
            duplicates (dict): Dictionary of duplicate files and their paths
        """
        self.logger.error("DUPLICATE FILES DETECTED!")
        self.logger.error(
            f"Found {len(duplicates)} duplicate filename(s) with {sum(len(paths) for paths in duplicates.values())} total files")

        for filename, paths in duplicates.items():
            self.logger.error(
                f"Duplicate file '{filename}' found in {len(paths)} locations:")
            for path in paths:
                self.logger.error(f"  - {path}")

        self.logger.error(
            "Data fetching failed due to duplicate files. Exiting...")
        sys.exit(1)

    def get_duplicate_summary(self) -> dict:
        """
        Get a summary of duplicate files without exiting.

        Returns:
            dict: Summary information about duplicates
        """
        duplicates = self._find_duplicate_files()

        return {
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "total_duplicate_files": sum(len(paths) for paths in duplicates.values()),
            "duplicates": duplicates
        }


def check_for_duplicate_files(output_folder: str = "committee_data") -> bool:
    """
    Convenience function to check for duplicate files.

    Args:
        output_folder (str): The folder to check for duplicate files

    Returns:
        bool: True if no duplicates found, False if duplicates detected (will exit on duplicates)
    """
    checker = DuplicateFileChecker(output_folder)
    return checker.check_for_duplicates()


if __name__ == "__main__":
    # For testing purposes
    checker = DuplicateFileChecker()
    summary = checker.get_duplicate_summary()
    print(f"Duplicate check summary: {summary}")

    if summary["has_duplicates"]:
        checker.check_for_duplicates()  # This will exit if duplicates found
