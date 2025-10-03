import zmq
import json


class ZMQClient:
    def __init__(self) -> None:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://127.0.0.1:5555")

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
