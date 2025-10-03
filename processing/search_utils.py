"""
Utility functions for search operations and result processing.
"""
from typing import Dict, Tuple
from processing.mk_database import get_mks
from utils.logger_config import get_logger

logger = get_logger(__name__)


def calculate_combined_score(similarity_score: float, importance_score: float) -> float:
    """Calculate combined relevance score from similarity and importance scores."""
    return similarity_score * importance_score


def process_search_results(distances, ids, df) -> Tuple[Dict, Dict, Dict]:
    """
    Process FAISS search results and organize by MK.

    Returns:
        Tuple of (mk_utterances, mk_total_scores, mk_metadata)
    """
    mk_utterances = {}  # mk_id -> list of (score, utterance_dict)
    mk_total_scores = {}  # mk_id -> total_score
    mk_metadata = {}  # mk_id -> (name, metadata)

    print("Search results:")
    print(f"DataFrame shape: {df.shape}")
    print(f"DataFrame index range: {df.index.min()} to {df.index.max()}")
    print(f"Number of search results: {len(ids[0])}")

    for rank, (uid, dist) in enumerate(zip(ids[0], distances[0]), start=1):
        utter_id = int(uid)

        row = df.loc[utter_id]
        similarity_score = float(dist)
        importance_score = row.get('importance_score', 1.0)
        combined_score = calculate_combined_score(
            similarity_score, importance_score)

        print(
            f"Match {rank}: ID {utter_id}, sim={similarity_score:.4f}, imp={importance_score:.4f}, "
            f"combined={combined_score:.4f}, Utterance: {row['text'][:120][::-1]} mk: {row['mk'][::-1]}")

        mk_id = str(row["mk_id"])

        if mk_id not in mk_utterances:
            mk_utterances[mk_id] = []
            mk_total_scores[mk_id] = 0.0
            mk_metadata[mk_id] = (row["mk"], get_mks().get(mk_id))

        utterance_data = {
            "text": row["text"],
            "src": row["src"],
            "relevance_score": combined_score
        }

        utterance_data["committee"] = str(row['committee'])
        utterance_data["subject"] = str(row['subject'])

        mk_utterances[mk_id].append((combined_score, utterance_data))
        mk_total_scores[mk_id] += combined_score

    for mk, val in mk_total_scores.items():
        max_score = max(score for score, _ in mk_utterances[mk])
        avg_score = val/len(mk_utterances[mk])
        context_score = (avg_score * 0.3) + (len(mk_utterances[mk])*0.0001)
        mk_total_scores[mk] = max_score+context_score

    return mk_utterances, mk_total_scores, mk_metadata


def build_sorted_results(mk_utterances: Dict, mk_total_scores: Dict, mk_metadata: Dict) -> Dict[str, Dict]:
    """
    Build final sorted results dictionary from processed data.

    Args:
        mk_utterances: Dictionary mapping mk_id to list of (score, utterance_dict) tuples
        mk_total_scores: Dictionary mapping mk_id to total relevance score
        mk_metadata: Dictionary mapping mk_id to (name, metadata) tuple

    Returns:
        Ordered dictionary of MK results sorted by total relevance score
    """
    utters_by_mk = {}

    # Sort MKs by total relevance score (descending - highest scores first)
    sorted_mk_ids = sorted(mk_total_scores.keys(),
                           key=lambda x: mk_total_scores[x], reverse=True)

    for mk_id in sorted_mk_ids:
        # Sort utterances by score (descending) and extract just the utterance data
        sorted_utterances = [
            utterance for _, utterance in sorted(mk_utterances[mk_id], key=lambda x: x[0], reverse=True)
        ]

        utters_by_mk[mk_id] = {
            "utterances": sorted_utterances,
            "name": mk_metadata[mk_id][0],
            "metadata": mk_metadata[mk_id][1],
            "total_relevance_score": mk_total_scores[mk_id],
        }

        # Log the MK with total score for debugging
        logger.info("MK: %s, Total relevance score: %.4f",
                    mk_metadata[mk_id][0], mk_total_scores[mk_id])

    # Log the final order for debugging
    logger.info("Final MK order (highest relevance first):")
    for i, (mk_id, mk_data) in enumerate(utters_by_mk.items(), 1):
        logger.info("%d. %s: %.4f", i,
                    mk_data['name'], mk_data['total_relevance_score'])

    return utters_by_mk
