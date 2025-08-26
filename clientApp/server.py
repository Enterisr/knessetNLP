from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

app = FastAPI()

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
    if not query:
        raise HTTPException(
            status_code=400, detail="Query parameter is required")
    return {"query": query, "response": f"Processed query: {query}"}


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
