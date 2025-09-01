from utils.logger_config import get_logger
from sklearn.cluster import HDBSCAN
import numpy as np
from typing import List, Tuple, Optional, Dict, Any


class Clusterer:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def cluster_npy_file(self):
