import os
import zmq
import json
import traceback
from processing.repo import init_repo, search
from utils.logger_config import get_logger
from processing.repo_data import RepoData

logger = get_logger(__name__)


def _resolve_bool_env(var_name: str, default: bool = False) -> bool:
    """Parse boolean-like environment variables."""
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def handle_search(repo_data: RepoData, request):
    """Handle search requests"""
    query = request.get("query", "")
    try:
        return search(repo_data, query)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Search error: {error_msg}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": error_msg}


def process_request(repo_data: RepoData, request_json):
    """Process incoming requests based on their command"""
    try:
        request = json.loads(request_json)
        return handle_search(repo_data, request)

    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON request"}
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "message": error_msg}


def init_repo_server(force_refresh: bool, host: str | None = None, port: int | None = None,init_repo_func=init_repo):
    """Start the ZeroMQ server and listen for requests"""
    host = host or os.getenv("REPO_HOST", "0.0.0.0")
    port = port or int(os.getenv("REPO_PORT", "5555"))

    logger.info("Starting ZeroMQ server on tcp://%s:%s", host, port)
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{host}:{port}")

    repo_data = init_repo_func(force_refresh)

    try:
        while True:
            request_json = socket.recv_string()
            logger.debug(f"Received request: {request_json}")

            response = process_request(repo_data, request_json)

            socket.send_string(json.dumps(response))

    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        socket.close()
        context.term()
        logger.info("Server terminated")



if __name__ == "__main__":
    force_refresh_env = _resolve_bool_env("FORCE_REFRESH", default=False)
    init_repo_server(force_refresh=force_refresh_env)
