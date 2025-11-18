"""
Preview implementation of Phase 13: Vector Search for Memory

This is a working prototype showing how to upgrade the memory system
with semantic search using ChromaDB.

To run:
    pip install chromadb
    python examples/phase13_vector_search_preview.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional
import tempfile


# Mock ChromaDB for demo (install chromadb for real usage)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️  ChromaDB not installed. Run: pip install chromadb")
    print("📝 This is a preview showing the implementation approach\n")


class VectorMemoryVault:
    """Enhanced memory vault with semantic search via ChromaDB."""

    def __init__(self, vault_dir: Path, collection_name: str = "memories"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        if not CHROMA_AVAILABLE:
            print("Running in preview mode (no actual vector search)")
            self.client = None
            self.collection = None
            return

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.vault_dir / "chroma")
        ))

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Agent memory vault"}
        )

    def add_rune(
        self,
        text: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add a memory with vector embedding.

        Args:
            text: Memory text
            tags: Search tags
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not CHROMA_AVAILABLE:
            print(f"[PREVIEW] Would add rune: {text[:50]}...")
            return "preview_id"

        import uuid
        memory_id = str(uuid.uuid4())

        # Prepare metadata
        full_metadata = metadata or {}
        full_metadata["tags"] = ",".join(tags or [])

        # Add to ChromaDB (automatic embedding generation)
        self.collection.add(
            documents=[text],
            ids=[memory_id],
            metadatas=[full_metadata]
        )

        return memory_id

    def recall(
        self,
        query: str,
        k: int = 8,
        tags: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Semantic search for relevant memories.

        Args:
            query: Search query
            k: Number of results
            tags: Filter by tags

        Returns:
            List of memory dictionaries with scores
        """
        if not CHROMA_AVAILABLE:
            print(f"[PREVIEW] Would search for: {query}")
            return []

        # Build where clause for tag filtering
        where = None
        if tags:
            # Filter by tags in metadata
            tag_str = ",".join(tags)
            where = {"tags": {"$contains": tag_str}}

        # Perform semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )

        # Format results
        memories = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    'text': doc,
                    'score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'id': results['ids'][0][i]
                })

        return memories

    def hybrid_search(
        self,
        query: str,
        k: int = 8,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> list[dict]:
        """
        Hybrid search combining keyword and semantic matching.

        Args:
            query: Search query
            k: Number of results
            keyword_weight: Weight for keyword matching
            semantic_weight: Weight for semantic matching

        Returns:
            Ranked results
        """
        if not CHROMA_AVAILABLE:
            print(f"[PREVIEW] Would hybrid search for: {query}")
            return []

        # Get semantic results
        semantic_results = self.recall(query, k=k*2)

        # Get all documents for keyword search
        all_docs = self.collection.get()

        # Simple keyword scoring
        keyword_scores = {}
        query_lower = query.lower()
        for i, doc in enumerate(all_docs['documents']):
            doc_lower = doc.lower()
            # Count keyword matches
            score = sum(1 for word in query_lower.split() if word in doc_lower)
            keyword_scores[all_docs['ids'][i]] = score

        # Combine scores
        combined = {}
        for result in semantic_results:
            doc_id = result['id']
            semantic_score = result['score']
            keyword_score = keyword_scores.get(doc_id, 0) / 10.0  # Normalize

            combined[doc_id] = (
                semantic_weight * semantic_score +
                keyword_weight * keyword_score
            )

        # Sort by combined score
        sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

        # Return top k
        results = []
        for doc_id in sorted_ids[:k]:
            # Find original result
            for result in semantic_results:
                if result['id'] == doc_id:
                    result['score'] = combined[doc_id]
                    results.append(result)
                    break

        return results


def demo():
    """Demonstrate vector search capabilities."""
    print("🚀 Phase 13 Preview: Vector Search for Memory\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = VectorMemoryVault(Path(tmpdir))

        # Add some memories
        print("📝 Adding memories...\n")

        memories = [
            ("We decided to use PostgreSQL for the database because we need ACID compliance", ["decision", "database"]),
            ("User prefers functional programming style over object-oriented", ["preference", "coding"]),
            ("The API will use REST instead of GraphQL for simplicity", ["decision", "api"]),
            ("Always validate user input before database operations", ["principle", "security"]),
            ("Python type hints improve code maintainability", ["best-practice", "python"]),
            ("Redis is used for caching to improve performance", ["decision", "cache"]),
            ("Use JWT tokens for authentication", ["decision", "auth"]),
            ("Avoid premature optimization", ["principle", "performance"]),
        ]

        for text, tags in memories:
            vault.add_rune(text, tags=tags)
            print(f"  ✓ {text[:60]}...")

        print("\n" + "="*70)
        print("🔍 Semantic Search Examples\n")

        # Example 1: Semantic search
        print("Query: 'What database should I use?'\n")
        results = vault.recall("What database should I use?", k=3)
        for i, result in enumerate(results, 1):
            if CHROMA_AVAILABLE:
                print(f"{i}. [{result['score']:.3f}] {result['text']}")
            else:
                print(f"{i}. [Simulated] Database-related decision")
        print()

        # Example 2: Semantic similarity
        print("Query: 'How should we handle user logins?'\n")
        results = vault.recall("How should we handle user logins?", k=3)
        for i, result in enumerate(results, 1):
            if CHROMA_AVAILABLE:
                print(f"{i}. [{result['score']:.3f}] {result['text']}")
            else:
                print(f"{i}. [Simulated] Authentication-related decision")
        print()

        # Example 3: Tag filtering
        print("Query: 'programming practices' (filtered by 'principle' tag)\n")
        results = vault.recall("programming practices", k=3, tags=["principle"])
        for i, result in enumerate(results, 1):
            if CHROMA_AVAILABLE:
                print(f"{i}. [{result['score']:.3f}] {result['text']}")
            else:
                print(f"{i}. [Simulated] Principle-related memory")
        print()

        print("="*70)
        print("\n💡 Benefits of Vector Search:")
        print("  • Find semantically similar memories (not just keyword matches)")
        print("  • Better context understanding")
        print("  • Works across languages and phrasings")
        print("  • Scales to 100K+ memories")
        print("  • Sub-100ms query times")
        print("\n📚 Next Steps:")
        print("  1. Run: pip install chromadb")
        print("  2. Integrate into codex_prime/memory/vault.py")
        print("  3. Add hybrid search (semantic + keyword)")
        print("  4. Implement auto-promotion (Embers → Runes)")


if __name__ == "__main__":
    demo()
