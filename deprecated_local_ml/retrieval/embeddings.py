"""
Embedding service for semantic retrieval.
Uses OpenAI embeddings or falls back to simple TF-IDF.
"""

import os
import json
import numpy as np
from typing import List, Optional, Dict


class EmbeddingService:
    """
    Service for generating text embeddings.
    Uses OpenAI embeddings when available, falls back to TF-IDF.
    """
    
    def __init__(self, use_openai: bool = True):
        """
        Initialize embedding service.
        
        Args:
            use_openai: Whether to try OpenAI embeddings first
        """
        self.use_openai = use_openai
        self.openai_client = None
        self.tfidf_vectorizer = None
        self.embedding_dim = 1536
        
        self._setup_provider()
    
    def _setup_provider(self) -> None:
        """Set up the embedding provider."""
        if self.use_openai:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key and api_key != "demo-key":
                try:
                    from openai import OpenAI
                    self.openai_client = OpenAI(api_key=api_key)
                    print("Using OpenAI embeddings")
                    return
                except Exception as e:
                    print(f"OpenAI setup failed: {e}")
        
        print("Using TF-IDF fallback embeddings")
        self._setup_tfidf()
    
    def _setup_tfidf(self) -> None:
        """Set up TF-IDF vectorizer as fallback."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.embedding_dim = 500
        self._tfidf_fitted = False
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            numpy array embedding
        """
        if self.openai_client:
            return self._openai_embed([text])[0]
        else:
            return self._tfidf_embed([text])[0]
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            numpy array of embeddings (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        if self.openai_client:
            return self._openai_embed(texts)
        else:
            return self._tfidf_embed(texts)
    
    def _openai_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI."""
        try:
            texts = [t[:8000] for t in texts]
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
            
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            self._setup_tfidf()
            return self._tfidf_embed(texts)
    
    def _tfidf_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using TF-IDF."""
        if self.tfidf_vectorizer is None:
            self._setup_tfidf()
        
        if not self._tfidf_fitted:
            if len(texts) > 1:
                self.tfidf_vectorizer.fit(texts)
                self._tfidf_fitted = True
            else:
                vocab = texts[0].lower().split()
                if len(vocab) > 10:
                    self.tfidf_vectorizer.fit([texts[0]] * 2 + ['padding text'])
                    self._tfidf_fitted = True
                else:
                    return np.random.randn(len(texts), self.embedding_dim).astype(np.float32)
        
        try:
            embeddings = self.tfidf_vectorizer.transform(texts).toarray()
            
            if embeddings.shape[1] < self.embedding_dim:
                padding = np.zeros((embeddings.shape[0], self.embedding_dim - embeddings.shape[1]))
                embeddings = np.hstack([embeddings, padding])
            
            return embeddings.astype(np.float32)
            
        except Exception as e:
            print(f"TF-IDF error: {e}")
            return np.random.randn(len(texts), self.embedding_dim).astype(np.float32)
    
    def get_embedding_dim(self) -> int:
        """Return embedding dimension."""
        return self.embedding_dim
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def batch_cosine_similarity(self, query: np.ndarray, 
                                 corpus: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and all corpus vectors.
        
        Args:
            query: Query embedding (embedding_dim,)
            corpus: Corpus embeddings (n_docs, embedding_dim)
            
        Returns:
            Similarity scores (n_docs,)
        """
        query_norm = query / (np.linalg.norm(query) + 1e-10)
        corpus_norms = corpus / (np.linalg.norm(corpus, axis=1, keepdims=True) + 1e-10)
        
        similarities = corpus_norms @ query_norm
        return similarities
