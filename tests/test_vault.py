"""Tests for MemoryVault."""

import pytest
import tempfile
from pathlib import Path
from codex_prime.memory.vault import MemoryVault, Memory


@pytest.fixture
def temp_vault():
    """Create temporary vault directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_vault_creation(temp_vault):
    """Test creating a memory vault."""
    vault = MemoryVault(temp_vault)
    assert vault.vault_dir == temp_vault
    assert vault.vault_dir.exists()


def test_add_ember(temp_vault):
    """Test adding embers."""
    vault = MemoryVault(temp_vault)
    vault.add_ember("Test ember 1")
    vault.add_ember("Test ember 2")

    embers = vault.get_recent_embers(10)
    assert len(embers) == 2
    assert "Test ember 1" in embers


def test_add_rune(temp_vault):
    """Test adding runes with tags."""
    vault = MemoryVault(temp_vault)
    vault.add_rune("Important decision", tags=["decision", "architecture"])

    runes = vault.get_runes_by_tags(["decision"])
    assert len(runes) == 1
    assert "Important decision" in runes


def test_add_glyph(temp_vault):
    """Test adding glyphs."""
    vault = MemoryVault(temp_vault)
    vault.add_glyph("Core principle: Be direct")

    glyphs = vault.get_glyphs()
    assert len(glyphs) == 1
    assert "Core principle" in glyphs[0]


def test_recall(temp_vault):
    """Test memory recall."""
    vault = MemoryVault(temp_vault)
    vault.add_ember("Quick note about API")
    vault.add_rune("API design decisions", tags=["api"])
    vault.add_glyph("Always document APIs")

    results = vault.recall("API", k=5)
    assert len(results) > 0
    assert any("API" in r for r in results)


def test_persistence(temp_vault):
    """Test vault persists across instances."""
    vault1 = MemoryVault(temp_vault)
    vault1.add_ember("Persistent ember")
    vault1.add_rune("Persistent rune", tags=["test"])
    vault1.add_glyph("Persistent glyph")

    # Create new vault instance
    vault2 = MemoryVault(temp_vault)

    assert len(vault2.get_recent_embers(10)) == 1
    assert len(vault2.get_runes_by_tags(["test"])) == 1
    assert len(vault2.get_glyphs()) == 1


def test_ember_ring_buffer(temp_vault):
    """Test ember ring buffer behavior."""
    vault = MemoryVault(temp_vault, max_embers=3)

    vault.add_ember("Ember 1")
    vault.add_ember("Ember 2")
    vault.add_ember("Ember 3")
    vault.add_ember("Ember 4")  # Should evict Ember 1

    embers = vault.get_recent_embers(10)
    assert len(embers) == 3
    assert "Ember 1" not in embers
    assert "Ember 4" in embers
