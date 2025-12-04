import faiss
import numpy as np
from typing import List, Tuple, Dict, Optional
import pickle
import os
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorStore:
    """FAISS-based vector store for medical knowledge retrieval"""
    
    def __init__(self, dimension: int = 384, index_type: str = "flat"):
        """
        Initialize vector store
        
        Args:
            dimension: Embedding dimension
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        self.dimension = dimension
        self.index_type = index_type
        
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "ivf":
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        elif index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self.is_trained = False
        
    def add_documents(self, texts: List[str], embeddings: np.ndarray, metadata: Optional[List[Dict]] = None):
        """
        Add documents to vector store
        
        Args:
            texts: List of document texts
            embeddings: Document embeddings
            metadata: Optional metadata for each document
        """
        if self.index_type == "ivf" and not self.is_trained:
            logger.info("Training IVF index...")
            self.index.train(embeddings)
            self.is_trained = True
        
        self.index.add(embeddings.astype('float32'))
        self.documents.extend(texts)
        
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{} for _ in texts])
        
        logger.info(f"✅ Added {len(texts)} documents. Total: {len(self.documents)}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (text, score, metadata) tuples
        """
        if len(self.documents) == 0:
            return []
        
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    float(dist),
                    self.metadata[idx]
                ))
        
        return results
    
    def save(self, path: str):
        """Save vector store to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.index")
        
        # Save documents and metadata
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'is_trained': self.is_trained
            }, f)
        
        logger.info(f"💾 Vector store saved to {path}")
    
    @classmethod
    def load(cls, path: str):
        """Load vector store from disk"""
        # Load metadata
        with open(f"{path}.pkl", 'rb') as f:
            data = pickle.load(f)
        
        # Create instance
        store = cls(dimension=data['dimension'], index_type=data['index_type'])
        store.index = faiss.read_index(f"{path}.index")
        store.documents = data['documents']
        store.metadata = data['metadata']
        store.is_trained = data['is_trained']
        
        logger.info(f"📂 Vector store loaded from {path} ({len(store.documents)} documents)")
        return store
