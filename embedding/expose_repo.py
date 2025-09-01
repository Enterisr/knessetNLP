import zmq
import json
import traceback
from embedding.repo import init_repo, search
from utils.logger_config import get_logger
from embedding.repo_data import RepoData

logger = get_logger(__name__)

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")


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


def init_repo_server(force_refresh: bool):
    """Start the ZeroMQ server and listen for requests"""
    logger.info("Starting ZeroMQ server on tcp://127.0.0.1:5555")

    repo_data = init_repo(force_refresh)

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
