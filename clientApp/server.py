import logging
import os

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn


from zmq_client import ZMQClient
from service import validate_and_sanitize_query, process_response_with_mk_sentiment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# React app build path
react_build_path = os.path.join(
    os.path.dirname(__file__), "kenessetData", "dist")


class Server:
    def __init__(self) -> None:
        """Initialize the FastAPI server with all routes and middleware"""
        self.app = FastAPI()
        self._setup_middleware()
        self._setup_static_files()
        self._setup_routes()
        self.zmq_client = ZMQClient()

    def _setup_middleware(self):
        """Configure CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_static_files(self):
        """Mount static files for the React frontend"""
        self.app.mount(
            "/assets", StaticFiles(directory=os.path.join(react_build_path, "assets")), name="assets")

    def _setup_routes(self):
        """Setup API routes"""
        self.app.add_api_route(
            "/api/query", self._handle_query, methods=["GET"])
        self.app.add_api_route("/{full_path:path}",
                               self._serve_spa, methods=["GET"])

    async def _handle_query(self, query: str = Query(None, description="Query to process")):
        """Handle API query requests"""
        try:
            sanitized_query = validate_and_sanitize_query(query)
            logger.info("Processing query: %s...",
                        (sanitized_query or "")[:50])
            res = self.zmq_client.req(query)

            # Process the response to add MK-level sentiment
            processed_res = process_response_with_mk_sentiment(res)

            return {"query": sanitized_query, "response": processed_res, "status": "success"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error processing query: %s", str(e))
            raise HTTPException(
                status_code=500, detail="An error occurred while processing your query")

    async def _serve_spa(self, full_path: str):
        """Serve SPA frontend for all non-API routes"""
        return FileResponse(os.path.join(react_build_path, "index.html"))


if __name__ == "__main__":
    # Create an instance of the server and expose the FastAPI app
    server = Server()
    app = server.app
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
