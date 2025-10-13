import zmq
import json
from config import ZMQ_SERVER


class ZMQClient:
    def __init__(self) -> None:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        print(f"Connecting to ZMQ server: {ZMQ_SERVER}")
        self.socket.connect(ZMQ_SERVER)

    def req(self, req: str, timeout=500000) -> dict:
        # Timeout in milliseconds
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        try:
            self.socket.send_string(json.dumps({"query": req}))
            response = self.socket.recv_string()
            return json.loads(response)
        except zmq.error.Again:
            # Handle timeout
            return {"error": "Request timed out"}
