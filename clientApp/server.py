import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from service import validate_and_sanitize_query
from embedding import init_repo_process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# React app build path
react_build_path = os.path.join(
    os.path.dirname(__file__), "kenessetData", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    logger.info("Starting the Repo!")
    try:
        init_repo_process(force_refresh=False)
        logger.info("Repo initialized.")
    except Exception as e:
        logger.exception("Failed to initialize repo on startup: %s", e)
        raise
    yield
    logger.info("Shutting down app...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static (Vite/React build)
app.mount("/assets", StaticFiles(directory=os.path.join(react_build_path,
          "assets")), name="assets")


@app.get("/api/query")
async def handle_query(query: str = Query(None, description="Query to process")):
    try:
        sanitized_query = validate_and_sanitize_query(query)
        logger.info("Processing query: %s...", (sanitized_query or "")[:50])
        response_text = f"Processed query: {sanitized_query}"
        return {"query": sanitized_query, "response": response_text, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error processing query: %s", str(e))
        raise HTTPException(
            status_code=500, detail="An error occurred while processing your query")


@app.get("/{full_path:path}")
async def serve_spa():
    return FileResponse(os.path.join(react_build_path, "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
