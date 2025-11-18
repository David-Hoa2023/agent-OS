"""Vector store implementation using ChromaDB for semantic search."""

from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorStore:
    """Vector database wrapper for semantic search."""

    def __init__(self, persist_directory: Path, collection_name: str = "memories"):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb"
            )

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.persist_directory)
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

    def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add document to vector store.

        Args:
            text: Document text
            metadata: Optional metadata
            doc_id: Optional document ID (generated if not provided)

        Returns:
            Document ID
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        # Prepare metadata
        meta = metadata or {}
        # Convert lists to comma-separated strings for ChromaDB
        for key, value in meta.items():
            if isinstance(value, list):
                meta[key] = ",".join(str(v) for v in value)

        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[doc_id]
        )

        return doc_id

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Search query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            List of results with text, score, metadata, and ID
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        # Format results
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    'text': results['documents'][0][i],
                    'score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'id': results['ids'][0][i]
                })

        return formatted

    def delete(self, doc_id: str) -> None:
        """Delete document by ID."""
        self.collection.delete(ids=[doc_id])

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        result = self.collection.get(ids=[doc_id])
        if result['documents']:
            return {
                'text': result['documents'][0],
                'metadata': result['metadatas'][0] if result['metadatas'] else {},
                'id': doc_id
            }
        return None

    def count(self) -> int:
        """Get total number of documents."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all documents."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )


class HybridSearch:
    """Combine keyword and semantic search for better results."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        n_results: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching.

        Args:
            query: Search query
            n_results: Number of results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            where: Optional metadata filter

        Returns:
            Ranked results
        """
        # Get semantic results (fetch more for reranking)
        semantic_results = self.vector_store.search(
            query,
            n_results=min(n_results * 2, 100),
            where=where
        )

        if not semantic_results:
            return []

        # Calculate keyword scores
        query_terms = set(query.lower().split())

        for result in semantic_results:
            text_terms = set(result['text'].lower().split())

            # Calculate keyword overlap (Jaccard similarity)
            intersection = len(query_terms & text_terms)
            union = len(query_terms | text_terms)
            keyword_score = intersection / union if union > 0 else 0

            # Combine scores
            semantic_score = result['score']
            combined_score = (
                semantic_weight * semantic_score +
                keyword_weight * keyword_score
            )

            result['semantic_score'] = semantic_score
            result['keyword_score'] = keyword_score
            result['score'] = combined_score

        # Sort by combined score and return top k
        semantic_results.sort(key=lambda x: x['score'], reverse=True)
        return semantic_results[:n_results]
