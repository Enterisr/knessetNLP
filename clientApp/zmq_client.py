import zmq
import zmq.asyncio
import json
import os
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
class AsyncZMQClient:
    def __init__(self) -> None:
        self.context = zmq.asyncio.Context()

    async def req(self, req: str, timeout=None) -> dict:
        socket = self.context.socket(zmq.REQ)
        socket.connect(os.environ.get("ZMQ_SERVER", "tcp://127.0.0.1:5555"))

        timeout =  int(os.environ.get("ZMQ_TIMEOUT", 500000))
        try:
            await socket.send_string(json.dumps({"query": req}))
            # Use asyncio timeout
            response = await asyncio.wait_for(
                socket.recv_string(), timeout=timeout / 1000.0
            )
            result = json.loads(response)
        except asyncio.TimeoutError:
            result = {"error": "Request timed out"}
        finally:
            socket.close()

        return result
