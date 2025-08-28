"""
Text embedding module.

This module handles text embeddings using SentenceTransformers
and provides functionality for vector similarity search and clustering.
"""

from .embedder import embed, Embedder

__all__ = ['embed', 'Embedder']
