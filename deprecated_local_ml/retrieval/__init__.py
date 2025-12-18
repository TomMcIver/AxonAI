"""
Retrieval Module - Embedding-based RAG for content retrieval.
Replaces keyword overlap with semantic similarity search.
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .retriever import ContentRetriever

__all__ = ['EmbeddingService', 'VectorStore', 'ContentRetriever']
