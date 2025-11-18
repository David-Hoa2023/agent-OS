"""Memory vault implementation with three-tier system."""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from collections import deque


@dataclass
class Memory:
    """Individual memory item."""

    text: str
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    tier: str = "ember"  # ember, rune, or glyph
    scope: str = "project"
    ttl: Optional[float] = None  # Time to live in seconds


class MemoryVault:
    """
    Three-tier memory system:
    - Embers: Short-term ring buffer with TTL
    - Runes: Medium-term tagged memories with vector search
    - Glyphs: Permanent curated knowledge
    """

    def __init__(self, vault_dir: Path, max_embers: int = 100):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        self.embers_file = self.vault_dir / "embers.jsonl"
        self.runes_file = self.vault_dir / "runes.jsonl"
        self.glyphs_file = self.vault_dir / "glyphs.json"

        self.max_embers = max_embers
        self.embers: deque[Memory] = deque(maxlen=max_embers)
        self.runes: list[Memory] = []
        self.glyphs: list[Memory] = []

        self._load_all()

    def _load_all(self) -> None:
        """Load all memory tiers from disk."""
        # Load embers
        if self.embers_file.exists():
            with open(self.embers_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.embers.append(Memory(**data))

        # Load runes
        if self.runes_file.exists():
            with open(self.runes_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.runes.append(Memory(**data))

        # Load glyphs
        if self.glyphs_file.exists():
            with open(self.glyphs_file, 'r') as f:
                data = json.load(f)
                self.glyphs = [Memory(**item) for item in data]

    def _save_embers(self) -> None:
        """Persist embers to disk."""
        with open(self.embers_file, 'w') as f:
            for ember in self.embers:
                f.write(json.dumps(asdict(ember)) + '\n')

    def _save_runes(self) -> None:
        """Persist runes to disk."""
        with open(self.runes_file, 'w') as f:
            for rune in self.runes:
                f.write(json.dumps(asdict(rune)) + '\n')

    def _save_glyphs(self) -> None:
        """Persist glyphs to disk."""
        with open(self.glyphs_file, 'w') as f:
            json.dump([asdict(g) for g in self.glyphs], f, indent=2)

    def add_ember(self, text: str, ttl: Optional[float] = 3600) -> None:
        """
        Add short-term memory (ring buffer with TTL).

        Args:
            text: Memory text
            ttl: Time to live in seconds (default 1 hour)
        """
        ember = Memory(text=text, tier="ember", ttl=ttl)
        self.embers.append(ember)
        self._save_embers()

    def add_rune(self, text: str, tags: Optional[list[str]] = None) -> None:
        """
        Add medium-term tagged memory.

        Args:
            text: Memory text
            tags: Search tags
        """
        rune = Memory(text=text, tags=tags or [], tier="rune")
        self.runes.append(rune)
        self._save_runes()

    def add_glyph(self, text: str) -> None:
        """
        Add permanent curated knowledge.

        Args:
            text: Knowledge text
        """
        glyph = Memory(text=text, tier="glyph")
        self.glyphs.append(glyph)
        self._save_glyphs()

    def recall(self, query: str, k: int = 8, tags: Optional[list[str]] = None) -> list[str]:
        """
        Recall relevant memories across all tiers.

        Args:
            query: Search query
            k: Number of results
            tags: Filter by tags

        Returns:
            List of memory texts
        """
        results = []
        current_time = time.time()

        # Add recent embers (filter by TTL)
        for ember in reversed(self.embers):
            if ember.ttl and (current_time - ember.timestamp) > ember.ttl:
                continue
            if query.lower() in ember.text.lower():
                results.append(ember.text)

        # Add matching runes
        for rune in self.runes:
            if tags and not any(tag in rune.tags for tag in tags):
                continue
            if query.lower() in rune.text.lower():
                results.append(rune.text)

        # Add all glyphs (they're always relevant)
        results.extend([g.text for g in self.glyphs])

        return results[:k]

    def get_recent_embers(self, n: int = 10) -> list[str]:
        """Get N most recent embers."""
        return [e.text for e in list(self.embers)[-n:]]

    def get_glyphs(self) -> list[str]:
        """Get all glyphs."""
        return [g.text for g in self.glyphs]

    def get_runes_by_tags(self, tags: list[str]) -> list[str]:
        """Get runes matching any of the provided tags."""
        results = []
        for rune in self.runes:
            if any(tag in rune.tags for tag in tags):
                results.append(rune.text)
        return results
