"""
Text embedding module.

This module handles text embeddings using SentenceTransformers
and provides functionality for vector similarity search and clustering.
"""

from .embedder import embed, Embedder
from .expose_repo import init_repo_server

__all__ = ['embed', 'Embedder', "init_repo_server"]
