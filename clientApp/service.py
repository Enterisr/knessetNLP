import bleach
from fastapi import HTTPException
import logging
import zmq
import json
import argparse
from typing import Dict, List, Any, Optional
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MAX_QUERY_LENGTH = 300
ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


def validate_and_sanitize_query(query: str) -> str:

    if not query:
        raise HTTPException(
            status_code=400, detail="Query parameter is required")

    # Check length limit
    if len(query) > MAX_QUERY_LENGTH:
        logger.warning(f"Query too long: {len(query)} characters")
        raise HTTPException(
            status_code=400,
            detail=f"Query too long. Maximum length is {MAX_QUERY_LENGTH} characters"
        )

    # Use bleach to clean the input (removes all HTML/script content)
    sanitized_query = bleach.clean(
        query,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Strip tags instead of escaping them
    )

    if not sanitized_query.strip():
        raise HTTPException(
            status_code=400, detail="Query contains no valid content")

    # Log if original query was modified (potential attack attempt)
    if sanitized_query != query.strip():
        logger.warning(
            f"Query was sanitized. Original length: {len(query)}, Sanitized length: {len(sanitized_query)}")

    return sanitized_query


def calculate_mk_sentiment(mk_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate overall sentiment for an MK based on their utterances.

    Args:
        mk_data: Dictionary containing MK data with utterances

    Returns:
        Average sentiment score (1-5 range: 1=very negative, 5=very positive) or None if no valid sentiments found
    """
    if not mk_data or 'utterances' not in mk_data:
        return None

    utterances = mk_data['utterances']
    if not isinstance(utterances, list) or len(utterances) == 0:
        return None

    sentiment_scores = []

    for utterance in utterances:
        if isinstance(utterance, dict) and 'sentiment' in utterance:
            sentiment = utterance['sentiment']

            # Handle different sentiment formats
            if isinstance(sentiment, (int, float)):
                # Assume it's already in 1-5 range
                sentiment_scores.append(float(sentiment))
            elif isinstance(sentiment, dict):
                # Legacy format with polarity/subjectivity - convert polarity from -1,1 to 1,5 range
                if 'polarity' in sentiment:
                    polarity = float(sentiment['polarity'])
                    # Convert from -1,1 range to 1,5 range: (polarity + 1) * 2 + 1
                    converted_sentiment = (polarity + 1) * 2 + 1
                    sentiment_scores.append(converted_sentiment)

    if not sentiment_scores:
        return None

    # Calculate average sentiment
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    # Ensure the result is within expected range (1-5)
    return max(1.0, min(5.0, average_sentiment))


def process_response_with_mk_sentiment(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the response data to add aggregated sentiment for each MK.

    Args:
        response_data: The response from the NLP service

    Returns:
        Modified response data with MK-level sentiment added
    """
    if not isinstance(response_data, dict):
        return response_data

    processed_data = response_data.copy()

    for mk_name, mk_data in processed_data.items():
        if isinstance(mk_data, dict):
            # Calculate and add sentiment for this MK
            mk_sentiment = calculate_mk_sentiment(mk_data)
            if mk_sentiment is not None:
                mk_data['sentiment'] = mk_sentiment
                logger.info(
                    f"Calculated sentiment for {mk_name}: {mk_sentiment:.3f}")
            else:
                logger.debug(f"No sentiment data available for {mk_name}")

    return processed_data
