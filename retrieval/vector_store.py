"""
Simple vector store for content embeddings.
Stores embeddings in database for retrieval.
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class VectorStore:
    """
    Simple in-memory vector store with database persistence.
    Stores document embeddings for similarity search.
    """
    
    def __init__(self, embedding_dim: int = 1536):
        """
        Initialize vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.documents: Dict[int, Dict] = {}
        self.embeddings: Dict[int, np.ndarray] = {}
    
    def add_document(self, doc_id: int, text: str, 
                     embedding: np.ndarray,
                     metadata: Optional[Dict] = None) -> None:
        """
        Add a document to the store.
        
        Args:
            doc_id: Unique document ID
            text: Document text
            embedding: Document embedding
            metadata: Optional metadata (source, type, etc.)
        """
        self.documents[doc_id] = {
            'text': text,
            'metadata': metadata or {},
            'added_at': datetime.utcnow().isoformat()
        }
        self.embeddings[doc_id] = embedding
    
    def remove_document(self, doc_id: int) -> bool:
        """Remove a document from the store."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            return True
        return False
    
    def search(self, query_embedding: np.ndarray, 
               top_k: int = 5,
               threshold: float = 0.0) -> List[Tuple[int, float, Dict]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (doc_id, similarity, document) tuples
        """
        if not self.embeddings:
            return []
        
        doc_ids = list(self.embeddings.keys())
        embeddings_matrix = np.array([self.embeddings[did] for did in doc_ids])
        
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        doc_norms = embeddings_matrix / (np.linalg.norm(embeddings_matrix, axis=1, keepdims=True) + 1e-10)
        
        similarities = doc_norms @ query_norm
        
        sorted_idx = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in sorted_idx:
            sim = similarities[idx]
            if sim >= threshold:
                doc_id = doc_ids[idx]
                results.append((doc_id, float(sim), self.documents[doc_id]))
        
        return results
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> Dict[int, Dict]:
        """Get all documents."""
        return self.documents.copy()
    
    def size(self) -> int:
        """Return number of documents in store."""
        return len(self.documents)
    
    def to_dict(self) -> Dict:
        """Serialize store to dictionary."""
        return {
            'embedding_dim': self.embedding_dim,
            'documents': self.documents,
            'embeddings': {
                str(k): v.tolist() for k, v in self.embeddings.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VectorStore':
        """Deserialize store from dictionary."""
        instance = cls(embedding_dim=data['embedding_dim'])
        instance.documents = data['documents']
        instance.embeddings = {
            int(k): np.array(v) for k, v in data['embeddings'].items()
        }
        return instance
    
    def save_to_db(self, db, class_id: int) -> None:
        """
        Save vector store to database.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID this store belongs to
        """
        from models import ContentEmbedding
        
        ContentEmbedding.query.filter_by(class_id=class_id).delete()
        
        for doc_id, doc in self.documents.items():
            embedding = self.embeddings.get(doc_id)
            if embedding is not None:
                ce = ContentEmbedding(
                    class_id=class_id,
                    content_file_id=doc_id,
                    chunk_text=doc['text'][:2000],
                    embedding_json=json.dumps(embedding.tolist()),
                    metadata_json=json.dumps(doc.get('metadata', {}))
                )
                db.session.add(ce)
        
        db.session.commit()
    
    @classmethod
    def load_from_db(cls, db, class_id: int) -> 'VectorStore':
        """
        Load vector store from database.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID to load store for
            
        Returns:
            VectorStore instance
        """
        from models import ContentEmbedding
        
        embeddings = ContentEmbedding.query.filter_by(class_id=class_id).all()
        
        instance = cls()
        
        for ce in embeddings:
            try:
                embedding = np.array(json.loads(ce.embedding_json))
                metadata = json.loads(ce.metadata_json) if ce.metadata_json else {}
                
                instance.add_document(
                    doc_id=ce.content_file_id or ce.id,
                    text=ce.chunk_text,
                    embedding=embedding,
                    metadata=metadata
                )
            except Exception as e:
                print(f"Error loading embedding {ce.id}: {e}")
        
        return instance
