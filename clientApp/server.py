from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
import logging
import bleach
import re

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
MAX_QUERY_LENGTH = 1000

# Allowed HTML tags and attributes for bleach (very restrictive for search queries)
ALLOWED_TAGS = []  # No HTML tags allowed in search queries
ALLOWED_ATTRIBUTES = {}  # No attributes allowed


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


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API route


@app.get("/api/query")
async def handle_query(query: str = Query(None, description="Query to process")):

    try:
        # Validate and sanitize the input
        sanitized_query = validate_and_sanitize_query(query)

        # Log successful query (truncated for security)
        logger.info(f"Processing query: {sanitized_query[:50]}...")

        # Process the query (placeholder - replace with your actual logic)
        response_text = f"Processed query: {sanitized_query}"

        return {
            "query": sanitized_query,
            "response": response_text,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your query"
        )


# React app build path
react_build_path = os.path.join(
    os.path.dirname(__file__), "kenessetData", "dist")

# Serve static assets (JS, CSS, images, etc.)
app.mount("/assets", StaticFiles(directory=os.path.join(react_build_path,
          "assets")), name="assets")

# Catch-all: serve React index.html for everything else


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(os.path.join(react_build_path, "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
