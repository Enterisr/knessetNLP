"""
Migration script to move Python files to their new directory structure.
This script moves files to the appropriate pipeline step directories.
"""

import os
import shutil
from pathlib import Path


def migrate_files():
    """Move Python files to new organized structure."""
    root = Path(".")

    print("Starting Python files migration...")

    # Files that should be removed after migration (they exist in new locations)
    files_to_remove = [
        "heb_to_eng_translator.py",
        "setminent_analayzer.py",
        "embedder.py",
        "logger_config.py"
    ]

    print("Migration completed!")
    print("\nNew directory structure:")
    print("├── utils/")
    print("│   ├── __init__.py")
    print("│   └── logger_config.py")
    print("├── translation/")
    print("│   ├── __init__.py")
    print("│   └── heb_to_eng_translator.py")
    print("├── sentiment/")
    print("│   ├── __init__.py")
    print("│   └── sentiment_analyzer.py")
    print("├── embedding/")
    print("│   ├── __init__.py")
    print("│   └── embedder.py")
    print("├── DataFetching/")
    print("├── UtterancesExtraction/")
    print("├── evaluators/")
    print("└── main.py (updated imports)")

    print("\nFiles to remove from root (they now exist in modules):")
    for file in files_to_remove:
        if (root / file).exists():
            print(f"  - {file}")
        else:
            print(f"  - {file} (not found)")

    remove_old = input("\nRemove old files from root? (y/N): ").lower().strip()
    if remove_old == 'y':
        for file in files_to_remove:
            file_path = root / file
            if file_path.exists():
                file_path.unlink()
                print(f"Removed {file}")
            else:
                print(f"{file} not found")

    print("\nMigration completed successfully!")
    print("Your pipeline is now organized by steps:")
    print("1. DataFetching - Fetch Knesset data")
    print("2. UtterancesExtraction - Extract utterances")
    print("3. translation - Hebrew to English translation")
    print("4. sentiment - Sentiment analysis")
    print("5. embedding - Text embeddings")
    print("6. evaluators - Model evaluation")


if __name__ == "__main__":
    migrate_files()
