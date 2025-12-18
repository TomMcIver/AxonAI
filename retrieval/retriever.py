"""
Content retriever using embeddings.
Replaces keyword-based retrieval with semantic similarity.
"""

import os
import re
import json
from typing import Dict, List, Optional

from .embeddings import EmbeddingService
from .vector_store import VectorStore


USE_EMBEDDING_RETRIEVAL = True


class ContentRetriever:
    """
    Semantic content retriever for RAG.
    Retrieves relevant content snippets using embedding similarity.
    """
    
    def __init__(self, use_embeddings: bool = None):
        """
        Initialize content retriever.
        
        Args:
            use_embeddings: Whether to use embedding-based retrieval
        """
        self.use_embeddings = use_embeddings if use_embeddings is not None else USE_EMBEDDING_RETRIEVAL
        self.embedding_service = None
        self.vector_stores: Dict[int, VectorStore] = {}
        
        if self.use_embeddings:
            self.embedding_service = EmbeddingService()
    
    def index_class_content(self, db, class_id: int) -> int:
        """
        Index all content for a class.
        
        Args:
            db: SQLAlchemy database instance
            class_id: Class ID to index
            
        Returns:
            Number of documents indexed
        """
        from models import ContentFile
        
        content_files = ContentFile.query.filter_by(class_id=class_id).all()
        
        store = VectorStore(embedding_dim=self.embedding_service.get_embedding_dim())
        doc_count = 0
        
        for cf in content_files:
            text = self._extract_file_content(cf)
            if not text:
                continue
            
            chunks = self._chunk_text(text)
            
            for i, chunk in enumerate(chunks):
                embedding = self.embedding_service.embed_text(chunk)
                
                doc_id = cf.id * 1000 + i
                store.add_document(
                    doc_id=doc_id,
                    text=chunk,
                    embedding=embedding,
                    metadata={
                        'source_name': cf.name,
                        'source_id': cf.id,
                        'chunk_index': i,
                        'file_type': cf.file_type
                    }
                )
                doc_count += 1
        
        self.vector_stores[class_id] = store
        
        try:
            store.save_to_db(db, class_id)
        except Exception as e:
            print(f"Failed to save embeddings to DB: {e}")
        
        return doc_count
    
    def retrieve(self, message: str, class_id: int, 
                 top_k: int = 3, db=None) -> List[Dict]:
        """
        Retrieve relevant content for a message.
        
        Args:
            message: User message/query
            class_id: Class ID to search in
            top_k: Number of results to return
            db: Optional database for lazy loading
            
        Returns:
            List of {source_name, snippet, score} dictionaries
        """
        if not self.use_embeddings or self.embedding_service is None:
            return self._keyword_retrieval(message, class_id, top_k, db)
        
        if class_id not in self.vector_stores and db is not None:
            try:
                self.vector_stores[class_id] = VectorStore.load_from_db(db, class_id)
            except Exception as e:
                print(f"Failed to load embeddings: {e}")
                return self._keyword_retrieval(message, class_id, top_k, db)
        
        store = self.vector_stores.get(class_id)
        if store is None or store.size() == 0:
            if db is not None:
                self.index_class_content(db, class_id)
                store = self.vector_stores.get(class_id)
            
            if store is None or store.size() == 0:
                return self._keyword_retrieval(message, class_id, top_k, db)
        
        query_embedding = self.embedding_service.embed_text(message)
        results = store.search(query_embedding, top_k=top_k, threshold=0.1)
        
        return [
            {
                'source_name': doc.get('metadata', {}).get('source_name', 'Unknown'),
                'snippet': doc['text'][:500] + ('...' if len(doc['text']) > 500 else ''),
                'score': round(score, 3)
            }
            for doc_id, score, doc in results
        ]
    
    def _keyword_retrieval(self, message: str, class_id: int, 
                           top_k: int, db) -> List[Dict]:
        """Fallback keyword-based retrieval."""
        if db is None:
            return []
        
        from models import ContentFile
        
        content_files = ContentFile.query.filter_by(class_id=class_id).all()
        if not content_files:
            return []
        
        message_words = set(re.findall(r'\b\w+\b', message.lower()))
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'can', 'to', 'of', 'in', 'for', 'on', 'with',
                     'at', 'by', 'from', 'as', 'and', 'but', 'if', 'or', 'because', 'this',
                     'that', 'these', 'those', 'what', 'which', 'who', 'i', 'me', 'my', 'you'}
        message_keywords = message_words - stop_words
        
        if not message_keywords:
            return []
        
        scored_snippets = []
        
        for cf in content_files:
            file_text = self._extract_file_content(cf)
            if not file_text:
                continue
            
            paragraphs = re.split(r'\n\s*\n|\n{2,}', file_text)
            if not paragraphs:
                paragraphs = [file_text[:2000]]
            
            for para in paragraphs:
                para = para.strip()
                if len(para) < 50:
                    continue
                
                para_words = set(re.findall(r'\b\w+\b', para.lower()))
                overlap = message_keywords & para_words
                score = len(overlap) / max(len(message_keywords), 1)
                
                if score > 0:
                    snippet = para[:500] + ('...' if len(para) > 500 else '')
                    scored_snippets.append({
                        'source_name': cf.name,
                        'snippet': snippet,
                        'score': round(score, 3)
                    })
        
        scored_snippets.sort(key=lambda x: x['score'], reverse=True)
        return scored_snippets[:top_k]
    
    def _extract_file_content(self, content_file) -> Optional[str]:
        """Extract text content from a ContentFile."""
        try:
            file_path = content_file.file_path
            if not file_path or not os.path.exists(file_path):
                return None
            
            file_type = (content_file.file_type or '').lower()
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_type == 'pdf' or file_ext == '.pdf':
                try:
                    import pypdf
                    with open(file_path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        text = ''
                        for page in reader.pages[:10]:
                            text += page.extract_text() or ''
                        return text[:10000]
                except ImportError:
                    return None
            
            elif file_ext in ['.txt', '.md', '.markdown']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[:10000]
            
            return None
            
        except Exception as e:
            print(f"Error extracting content from {content_file.name}: {e}")
            return None
    
    def _chunk_text(self, text: str, chunk_size: int = 500, 
                    overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in words
            overlap: Number of overlapping words
            
        Returns:
            List of text chunks
        """
        paragraphs = re.split(r'\n\s*\n|\n{2,}', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            words = para.split()
            
            if current_size + len(words) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_words
                current_size = len(overlap_words)
            
            current_chunk.extend(words)
            current_size += len(words)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text[:2000]]
    
    def clear_cache(self, class_id: Optional[int] = None) -> None:
        """Clear cached vector stores."""
        if class_id is not None:
            self.vector_stores.pop(class_id, None)
        else:
            self.vector_stores.clear()
