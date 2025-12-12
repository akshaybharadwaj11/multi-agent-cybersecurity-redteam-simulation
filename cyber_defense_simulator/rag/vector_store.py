"""
Vector Store Implementation for RAG System
Supports ChromaDB for production and in-memory for testing
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path
import logging

from core.config import Config
from rag.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for threat intelligence and runbooks"""
    
    def __init__(self, collection_name: str = "cyber_defense_kb"):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the collection to use
        """
        self.collection_name = collection_name
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=Config.VECTOR_STORE_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=None  # We'll handle embeddings manually
            )
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Cyber defense knowledge base"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to vector store
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
        """
        if not documents:
            return
        
        # Generate embeddings
        embeddings = self.embedding_generator.embed_documents(documents)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to {self.collection_name}")
    
    def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict] = None
    ) -> List[Tuple[str, Dict, float]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of (document, metadata, score) tuples
        """
        if top_k is None:
            top_k = Config.TOP_K_RETRIEVAL
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed_query(query)
        
        # Search - handle filters properly for ChromaDB
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k * 2  # Get more results to filter
        }
        
        # ChromaDB filter format
        if filters:
            where_clause = {}
            for key, value in filters.items():
                where_clause[key] = {"$eq": value}
            query_kwargs["where"] = where_clause
        
        results = self.collection.query(**query_kwargs)
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0 and results['documents'][0]:
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                # Convert distance to similarity score (0-1)
                similarity = 1 / (1 + distance)
                formatted_results.append((doc, metadata, similarity))
        
        # Limit to top_k
        return formatted_results[:top_k]
    
    def search_by_mitre_technique(
        self,
        technique_id: str,
        top_k: int = None
    ) -> List[Tuple[str, Dict, float]]:
        """
        Search for documents related to a MITRE ATT&CK technique
        
        Args:
            technique_id: MITRE technique ID (e.g., T1566)
            top_k: Number of results
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = 5
        
        # Do semantic search for runbooks
        query = f"MITRE ATT&CK {technique_id} detection and remediation runbook"
        
        # Search all documents first
        all_results = self.search(
            query=query,
            top_k=top_k * 5,  # Get many results to filter
            filters=None
        )
        
        # Filter to runbooks and check if technique matches
        runbook_results = []
        base_technique = technique_id.split('.')[0]  # Get base technique (e.g., T1566 from T1566.001)
        
        for doc, metadata, score in all_results:
            if metadata.get('type') == 'runbook':
                # Check if this runbook applies to this technique
                techniques_str = metadata.get('techniques', '')
                if technique_id in techniques_str or base_technique in techniques_str:
                    runbook_results.append((doc, metadata, score))
                    if len(runbook_results) >= top_k:
                        break
        
        # If no exact matches, return top runbooks by relevance
        if not runbook_results:
            for doc, metadata, score in all_results:
                if metadata.get('type') == 'runbook':
                    runbook_results.append((doc, metadata, score))
                    if len(runbook_results) >= top_k:
                        break
        
        logger.info(f"Found {len(runbook_results)} runbooks for technique {technique_id}")
        return runbook_results
    
    def search_similar_incidents(
        self,
        incident_description: str,
        top_k: int = 3
    ) -> List[Tuple[str, Dict, float]]:
        """
        Find similar past incidents
        
        Args:
            incident_description: Description of current incident
            top_k: Number of similar incidents to retrieve
            
        Returns:
            List of similar incidents
        """
        return self.search(
            query=incident_description,
            top_k=top_k,
            filters={"type": "incident"}
        )
    
    def get_document_count(self) -> int:
        """Get total number of documents in store"""
        return self.collection.count()
    
    def delete_collection(self) -> None:
        """Delete the entire collection"""
        self.client.delete_collection(name=self.collection_name)
        logger.warning(f"Deleted collection: {self.collection_name}")
    
    def reset(self) -> None:
        """Reset the vector store"""
        try:
            self.delete_collection()
        except Exception:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Cyber defense knowledge base"}
        )
        logger.info(f"Reset collection: {self.collection_name}")


class InMemoryVectorStore:
    """Simple in-memory vector store for testing"""
    
    def __init__(self):
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []
        self.embeddings: List[np.ndarray] = []
        self.ids: List[str] = []
        self.embedding_generator = EmbeddingGenerator()
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to in-memory store"""
        embeddings = self.embedding_generator.embed_documents(documents)
        
        if ids is None:
            ids = [f"doc_{len(self.documents) + i}" for i in range(len(documents))]
        
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.embeddings.extend(embeddings)
        self.ids.extend(ids)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Tuple[str, Dict, float]]:
        """Search using cosine similarity"""
        if not self.documents:
            return []
        
        query_embedding = self.embedding_generator.embed_query(query)
        
        # Calculate cosine similarities
        similarities = []
        for emb in self.embeddings:
            similarity = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            similarities.append(similarity)
        
        # Sort by similarity
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Apply filters if provided
        results = []
        for idx in sorted_indices:
            if filters:
                if all(self.metadatas[idx].get(k) == v for k, v in filters.items()):
                    results.append((
                        self.documents[idx],
                        self.metadatas[idx],
                        similarities[idx]
                    ))
            else:
                results.append((
                    self.documents[idx],
                    self.metadatas[idx],
                    similarities[idx]
                ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_document_count(self) -> int:
        """Get document count"""
        return len(self.documents)
    
    def reset(self) -> None:
        """Clear all documents"""
        self.documents = []
        self.metadatas = []
        self.embeddings = []
        self.ids = []
