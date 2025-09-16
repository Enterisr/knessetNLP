import zmq
import json
import argparse


def create_zmq_client():
    """Create a ZeroMQ client that connects to the repository server"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")
    return socket


def send_search_request(socket, query):
    """Send a search request to the server"""
    request = {
        "command": "search",
        "query": query
    }

    # Send the request
    socket.send_string(json.dumps(request))

    # Receive and parse the response
    response = socket.recv_string()
    return json.loads(response)


def main():
    parser = argparse.ArgumentParser(
        description="Client for the embedding repository server")
    parser.add_argument("query", nargs="?", default="",
                        help="Search query to send to the server")
    args = parser.parse_args()

    socket = create_zmq_client()

    # If no query provided, enter interactive mode
    if not args.query:
        print("ZeroMQ Repository Client")
        print("Type 'exit' or 'quit' to exit")
        print("Enter search queries below:")

        while True:
            try:
                query = input("> ")
                if query.lower() in ["exit", "quit"]:
                    break

                response = send_search_request(socket, query)
                print(json.dumps(response, indent=2, ensure_ascii=False))
            except KeyboardInterrupt:
                break
            except zmq.ZMQError as e:
                print(f"ZMQ Error: {str(e)}")
            except json.JSONDecodeError as e:
                print(f"JSON Error: {str(e)}")
            except ConnectionError as e:
                print(f"Connection Error: {str(e)}")
    else:
        # Single query mode
        response = send_search_request(socket, args.query)
        print(json.dumps(response, indent=2, ensure_ascii=False))

    # Clean up
    socket.close()


if __name__ == "__main__":
    main()
