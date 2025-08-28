"""
Migration script to clean up old Python files from root after refactoring
"""
import os
import shutil
from pathlib import Path


def cleanup_old_files():
    """Remove the old Python files that have been moved to new modules"""

    root = Path(".")

    # Files that should be removed (they've been moved to new modules)
    old_files = [
        "embedder.py",
        "setminent_analayzer.py",
        "heb_to_eng_translator.py",
        "logger_config.py"
    ]

    print("🧹 Cleaning up old Python files...")

    for file_name in old_files:
        file_path = root / file_name
        if file_path.exists():
            print(f"  ✅ Removing {file_name}")
            file_path.unlink()
        else:
            print(f"  ❌ {file_name} not found")

    # Remove the old core directory if it was created
    old_core = root / "core"
    if old_core.exists():
        print(f"  🗂️  Removing old core directory")
        shutil.rmtree(old_core)

    print("\n📁 Current structure after cleanup:")
    print("Root Python files that remain:")
    python_files = list(root.glob("*.py"))
    for py_file in python_files:
        print(f"  📄 {py_file.name}")

    print("\nModule directories:")
    modules = ["utils", "translation", "sentiment", "embedding",
               "DataFetching", "UtterancesExtraction", "evaluators"]
    for module in modules:
        module_path = root / module
        if module_path.exists():
            print(f"  📦 {module}/")
            py_files = list(module_path.glob("*.py"))
            for py_file in py_files:
                print(f"    📄 {py_file.name}")

    print("\nData files remain in root (as intended):")
    data_files = ["utterances_data.pkl", "mk_utterances.jsonl", "embeddings.npy",
                  "committie_index", "mks_data.json", "sentiment_analysis_results.json"]
    for data_file in data_files:
        if (root / data_file).exists():
            print(f"  📊 {data_file}")

    print("\nData directories remain in root (as intended):")
    data_dirs = ["utterances", "committee_data", "logs", "temp"]
    for data_dir in data_dirs:
        if (root / data_dir).exists():
            print(f"  📁 {data_dir}/")


if __name__ == "__main__":
    cleanup_old_files()
