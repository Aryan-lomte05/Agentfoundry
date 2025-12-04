from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global embedder instance
_embedder = None

def get_embedder():
    """Get or create sentence embedder"""
    global _embedder
    
    if _embedder is None:
        logger.info("🔧 Loading sentence transformer model...")
        _embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("✅ Embedder loaded")
    
    return _embedder

def embed_text(text: str) -> np.ndarray:
    """
    Embed single text
    
    Args:
        text: Input text
        
    Returns:
        np.ndarray: Embedding vector
    """
    embedder = get_embedder()
    return embedder.encode(text, convert_to_numpy=True)

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed multiple texts
    
    Args:
        texts: List of input texts
        
    Returns:
        np.ndarray: Matrix of embedding vectors
    """
    embedder = get_embedder()
    return embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
