"""Tests for vector search functionality."""

import pytest
import tempfile
from pathlib import Path

try:
    from codex_prime.memory.enhanced_vault import EnhancedMemoryVault
    from codex_prime.memory.vector_store import VectorStore, HybridSearch
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False


@pytest.fixture
def temp_vault():
    """Create temporary vault directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_vector_store_creation(temp_vault):
    """Test creating a vector store."""
    store = VectorStore(temp_vault / "vectors", "test_collection")
    assert store.count() == 0


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_vector_store_add_and_search(temp_vault):
    """Test adding and searching documents."""
    store = VectorStore(temp_vault / "vectors", "test")

    # Add documents
    doc1_id = store.add("Python is a programming language", {"category": "tech"})
    doc2_id = store.add("Cats are great pets", {"category": "animals"})
    doc3_id = store.add("JavaScript is also a programming language", {"category": "tech"})

    assert store.count() == 3

    # Search for programming
    results = store.search("coding and programming", n_results=2)
    assert len(results) <= 2
    # Should find programming-related docs
    texts = [r['text'] for r in results]
    assert any("programming" in text for text in texts)


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_hybrid_search(temp_vault):
    """Test hybrid search combining semantic and keyword."""
    store = VectorStore(temp_vault / "vectors", "test")
    hybrid = HybridSearch(store)

    # Add documents
    store.add("PostgreSQL is a relational database", {"type": "database"})
    store.add("MongoDB is a document database", {"type": "database"})
    store.add("Python uses dynamic typing", {"type": "language"})

    # Search with hybrid
    results = hybrid.search("database systems", n_results=2)
    assert len(results) <= 2

    # Check that both scores are present
    if results:
        assert 'semantic_score' in results[0]
        assert 'keyword_score' in results[0]
        assert 'score' in results[0]


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_enhanced_vault_creation(temp_vault):
    """Test creating enhanced vault."""
    vault = EnhancedMemoryVault(temp_vault, use_vector_search=True)
    stats = vault.get_stats()

    assert stats['total_embers'] == 0
    assert stats['total_runes'] == 0
    assert stats['total_glyphs'] == 0
    assert stats['vector_search_enabled'] == True


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_enhanced_vault_semantic_recall(temp_vault):
    """Test semantic recall in enhanced vault."""
    vault = EnhancedMemoryVault(temp_vault, use_vector_search=True)

    # Add some runes
    vault.add_rune("We decided to use PostgreSQL for the database", tags=["decision", "database"])
    vault.add_rune("The API will use REST instead of GraphQL", tags=["decision", "api"])
    vault.add_rune("Python is the primary language", tags=["decision", "language"])

    # Semantic search
    results = vault.recall("What database should we use?", k=2, use_semantic=True)

    assert len(results) > 0
    # Should find the PostgreSQL decision
    texts = [r['text'] for r in results]
    assert any("PostgreSQL" in text for text in texts)


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_auto_promotion(temp_vault):
    """Test auto-promotion from ember to rune."""
    vault = EnhancedMemoryVault(temp_vault, auto_promote_threshold=3)

    # Add same content multiple times
    text = "Important pattern: Always validate user input"

    vault.add_ember(text)
    vault.add_ember(text)
    vault.add_ember(text)  # Should trigger auto-promotion

    stats = vault.get_stats()
    assert stats['total_runes'] >= 1  # Should have been promoted


def test_enhanced_vault_fallback_without_vector(temp_vault):
    """Test enhanced vault works without vector search."""
    vault = EnhancedMemoryVault(temp_vault, use_vector_search=False)

    vault.add_rune("Test memory", tags=["test"])
    results = vault.recall("Test", k=5, use_semantic=False)

    assert len(results) > 0


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_enhanced_vault_persistence(temp_vault):
    """Test vault persists vector data across instances."""
    # First instance
    vault1 = EnhancedMemoryVault(temp_vault, use_vector_search=True)
    vault1.add_rune("Persistent memory test", tags=["test"])

    # Second instance
    vault2 = EnhancedMemoryVault(temp_vault, use_vector_search=True)
    results = vault2.recall("persistent", k=5)

    assert len(results) > 0
    texts = [r['text'] for r in results]
    assert any("Persistent memory test" in text for text in texts)


@pytest.mark.skipif(not VECTOR_AVAILABLE, reason="ChromaDB not installed")
def test_vault_stats(temp_vault):
    """Test vault statistics."""
    vault = EnhancedMemoryVault(temp_vault, use_vector_search=True)

    vault.add_ember("Ember 1")
    vault.add_rune("Rune 1", tags=["test"])
    vault.add_glyph("Glyph 1")

    stats = vault.get_stats()

    assert stats['total_embers'] == 1
    assert stats['total_runes'] == 1
    assert stats['total_glyphs'] == 1
    assert stats['vector_count'] == 1  # One rune in vector store
