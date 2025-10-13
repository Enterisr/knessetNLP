import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# ZMQ configuration
ZMQ_SERVER = os.environ.get("ZMQ_SERVER", "tcp://127.0.0.1:5555")