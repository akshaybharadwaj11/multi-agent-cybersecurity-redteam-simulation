"""
Embedding Generation for RAG System
Supports OpenAI embeddings and sentence-transformers as fallback
"""

import openai
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

from core.config import Config

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text"""
    
    def __init__(self, use_openai: bool = True):
        """
        Initialize embedding generator
        
        Args:
            use_openai: Whether to use OpenAI embeddings (requires API key)
        """
        self.use_openai = use_openai and bool(Config.OPENAI_API_KEY)
        
        if self.use_openai:
            openai.api_key = Config.OPENAI_API_KEY
            self.model = Config.EMBEDDING_MODEL
            logger.info(f"Using OpenAI embeddings: {self.model}")
        else:
            # Fallback to sentence-transformers
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Using sentence-transformers: all-MiniLM-L6-v2")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.use_openai:
            return self._embed_openai(texts)
        else:
            return self._embed_sentence_transformer(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        return self.embed_documents([text])[0]
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            response = openai.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Fallback to sentence-transformers
            logger.info("Falling back to sentence-transformers")
            self.use_openai = False
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            return self._embed_sentence_transformer(texts)
    
    def _embed_sentence_transformer(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_embedding_dim(self) -> int:
        """Get dimensionality of embeddings"""
        if self.use_openai:
            # OpenAI text-embedding-3-small: 1536 dimensions
            return 1536
        else:
            # all-MiniLM-L6-v2: 384 dimensions
            return 384
