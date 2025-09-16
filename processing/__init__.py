"""
Text embedding module.

This module handles text embeddings using SentenceTransformers
and provides functionality for vector similarity search and clustering.
"""

from .embedder import embed, Embedder
from .expose_repo import init_repo_server
from .tf_idf_nisui import run_tf_idf_analysis
__all__ = ['embed', 'Embedder',  "expose_repo",
           "init_repo_server", "run_tf_idf_analysis"]
