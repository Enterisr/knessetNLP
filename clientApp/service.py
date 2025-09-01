import bleach
from fastapi import HTTPException
import logging

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
