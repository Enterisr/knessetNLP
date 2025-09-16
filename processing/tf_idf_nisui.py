"""
Module for running TF-IDF analysis on committee files.
This script processes complete committee transcription files rather than individual utterances.
"""
# Standard library imports
import gc
import json
import os
from pathlib import Path

# Third-party imports
import faiss
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

# Local application imports
from utils.logger_config import get_logger

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
logger = get_logger(__name__)


def _discover_partitions(committee_folder: str) -> dict:
    """
    Discover all partitions and their files.

    Returns:
        Dict mapping partition names to list of (file_name, full_file_path) tuples
    """
    partitions = {}
    items_in_output = os.listdir(committee_folder)
    partition_folders = [
        item for item in items_in_output
        if item.startswith("part_") and os.path.isdir(os.path.join(committee_folder, item))
    ]

    if not partition_folders:
        raise ValueError(
            f"No partition folders found in {committee_folder}. Expected folders named 'part_0', 'part_1', etc.")

    logger.info("Found %d partition folders: %s", len(
        partition_folders), sorted(partition_folders))

    for partition_folder in sorted(partition_folders):
        partition_path = os.path.join(committee_folder, partition_folder)
        partition_files = []
        for file_name in os.listdir(partition_path):
            if file_name.endswith(".json"):
                full_path = os.path.join(partition_path, file_name)
                partition_files.append((file_name, full_path))

        if partition_files:  # Only add if there are files
            partitions[partition_folder] = partition_files

    return partitions


def _process_committee_file(file_path: str) -> str:
    """
    Process a single committee protocol JSON file to extract the full text.

    Args:
        file_path: Path to input JSON file

    Returns:
        Full text content of the committee file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            protocol_data = json.load(f)

        # Return the full text of the committee file
        return protocol_data.get("text", "")
    except (IOError, json.JSONDecodeError, KeyError) as e:
        logger.error("Error processing %s: %s", file_path, str(e))
        return ""


def load_committee_texts(committee_folder="committee_data"):
    """
    Load all committee texts from the committee_data folder.

    Args:
        committee_folder: Folder containing partition folders with protocol JSON files

    Returns:
        List of committee texts
    """
    partitions = _discover_partitions(committee_folder)

    if not partitions:
        logger.warning("No JSON files found in %s", committee_folder)
        return []

    total_files = sum(len(files) for files in partitions.values())
    logger.info("Found %d partitions with %d total JSON files to process",
                len(partitions), total_files)

    committee_texts = []
    committee_metadata = []

    for partition_name, files_list in partitions.items():
        for file_name, file_path in files_list:
            text = _process_committee_file(file_path)
            if text:
                committee_texts.append(text)
                committee_metadata.append({
                    "file_name": file_name,
                    "partition": partition_name,
                    "path": file_path
                })

    logger.info(f"Loaded {len(committee_texts)} committee texts")

    # Save metadata for later reference
    with open(PROJECT_ROOT / "committee_metadata.json", "w", encoding="utf-8") as f:
        json.dump(committee_metadata, f, ensure_ascii=False, indent=2)

    return committee_texts


def embed_in_tf_idf(committee_texts, query_text="מכבי אש בחדרה", top_k=100):
    """
    Embed committee texts using TF-IDF and perform a search with the given query.

    Args:
        committee_texts: List of committee texts to embed
        query_text: The query to search for
        top_k: Number of top results to return

    Returns:
        Tuple of (distances, indices, feature_names)
    """
    logger.info(
        f"Creating TF-IDF embeddings for {len(committee_texts)} committee texts")

    # Use float32 for better compatibility with FAISS
    vectorizer = TfidfVectorizer(dtype=np.float32)
    X = vectorizer.fit_transform(committee_texts)
    X_dense = X.toarray()

    # Create FAISS index for fast similarity search
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X_dense)

    # Transform query text
    y = vectorizer.transform([query_text])
    y_dense = y.toarray().astype(np.float32)

    # Search for similar documents
    # D is distances, I is indices
    D, I = index.search(y_dense, min(top_k, len(committee_texts)))

    # Get feature names for interpretation
    feature_names = vectorizer.get_feature_names_out()

    logger.info(f"Found {len(I[0])} matches for query: '{query_text}'")

    return D, I, feature_names, vectorizer


def print_search_results(D, I, committee_metadata, query_text, top_n=10):
    """
    Print search results in a readable format.

    Args:
        D: Distances array from FAISS search
        I: Indices array from FAISS search
        committee_metadata: List of metadata for each committee file
        query_text: The query that was searched
        top_n: Number of top results to print
    """
    print(f"\nTop {top_n} results for query: '{query_text}'\n")
    print("-" * 80)

    # Take only the first row as we only have one query
    distances = D[0][:top_n]
    indices = I[0][:top_n]

    for i, (idx, dist) in enumerate(zip(indices, distances)):
        if idx < len(committee_metadata):
            metadata = committee_metadata[idx]
            print(f"{i+1}. Score: {dist:.4f}")
            print(f"   File: {metadata['file_name']}")
            print(f"   Partition: {metadata['partition']}")
            print("-" * 80)


def analyze_feature_importance(vectorizer, I, committee_texts, top_n_features=20):
    """
    Analyze and print the most important features (terms) in the matched documents.

    Args:
        vectorizer: Fitted TF-IDF vectorizer
        I: Indices array from FAISS search
        committee_texts: List of committee texts
        top_n_features: Number of top features to print
    """
    # Get indices of top matching documents
    doc_indices = I[0][:10]  # Use top 10 documents

    # Get feature names
    feature_names = vectorizer.get_feature_names_out()

    print("\nMost important terms in matching documents:")
    print("-" * 80)

    # For each top document
    for i, doc_idx in enumerate(doc_indices):
        if doc_idx < len(committee_texts):
            # Transform the document to get its TF-IDF vector
            doc_vector = vectorizer.transform([committee_texts[doc_idx]])

            # Get indices of features sorted by importance (TF-IDF score)
            feature_indices = doc_vector.toarray(
            )[0].argsort()[-top_n_features:][::-1]

            print(f"Document {i+1} important terms:")
            for j, feature_idx in enumerate(feature_indices):
                if feature_idx < len(feature_names):
                    # Print term and its TF-IDF score
                    print(
                        f"   {j+1}. {feature_names[feature_idx]} ({doc_vector[0, feature_idx]:.4f})")
            print("-" * 80)


def run_tf_idf_analysis(committee_folder="committee_data", query_text="מערך הטילים המדויקים של החיזבאללה", top_k=100):
    """
    Run TF-IDF analysis on committee files.

    Args:
        committee_folder: Folder containing committee files
        query_text: Query text to search for
        top_k: Number of top results to return
    """
    # Load committee texts
    committee_texts = load_committee_texts(committee_folder)

    if not committee_texts:
        logger.error("No committee texts found. Exiting.")
        return

    # Load metadata
    try:
        with open(PROJECT_ROOT / "committee_metadata.json", "r", encoding="utf-8") as f:
            committee_metadata = json.load(f)
    except FileNotFoundError:
        committee_metadata = [{"file_name": f"doc_{i}", "partition": "unknown"}
                              for i in range(len(committee_texts))]

    # Perform TF-IDF embedding and search
    D, I, feature_names, vectorizer = embed_in_tf_idf(
        committee_texts, query_text, top_k)

    # Print top matching terms
    print("\nTop matching terms for query:")
    for idx in I[0][:20]:  # Show top 20 matching terms
        if idx < len(feature_names):
            print(f"- {feature_names[idx]}")

    # Print search results
    print_search_results(D, I, committee_metadata, query_text)

    # Analyze feature importance
    analyze_feature_importance(vectorizer, I, committee_texts)
