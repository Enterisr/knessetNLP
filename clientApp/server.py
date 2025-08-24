from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the React app's static files
react_build_path = os.path.join(
    os.path.dirname(__file__), "kenessetData", "public")
app.mount("/", StaticFiles(directory=react_build_path,
          html=True), name="react_app")


@app.get("/api/query")
async def handle_query(query: str = Query(None, description="Query to process")):
    if not query:
        return {"error": "Query parameter is required"}, 400

    # TODO: Process the query here
    # This is a placeholder for your actual query processing logic
    result = {
        "query": query,
        "response": f"Processed query: {query}"
    }

    return result

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
