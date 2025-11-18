"""Enhanced Memory Vault with vector search capabilities."""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import deque, Counter

from .vault import Memory

try:
    from .vector_store import VectorStore, HybridSearch
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False


class EnhancedMemoryVault:
    """
    Enhanced three-tier memory system with semantic search:
    - Embers: Short-term ring buffer with TTL
    - Runes: Medium-term with vector search
    - Glyphs: Permanent curated knowledge
    """

    def __init__(
        self,
        vault_dir: Path,
        max_embers: int = 100,
        use_vector_search: bool = True,
        auto_promote_threshold: int = 3
    ):
        """
        Initialize enhanced vault.

        Args:
            vault_dir: Directory for vault storage
            max_embers: Maximum number of embers to keep
            use_vector_search: Enable vector search for runes
            auto_promote_threshold: Reference count to auto-promote ember to rune
        """
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        self.embers_file = self.vault_dir / "embers.jsonl"
        self.runes_file = self.vault_dir / "runes.jsonl"
        self.glyphs_file = self.vault_dir / "glyphs.json"
        self.stats_file = self.vault_dir / "stats.json"

        self.max_embers = max_embers
        self.auto_promote_threshold = auto_promote_threshold

        # Initialize tiers
        self.embers: deque[Memory] = deque(maxlen=max_embers)
        self.runes: List[Memory] = []
        self.glyphs: List[Memory] = []

        # Reference counting for auto-promotion
        self.reference_counts: Counter = Counter()

        # Initialize vector store for runes if available
        self.use_vector_search = use_vector_search and VECTOR_AVAILABLE
        if self.use_vector_search:
            try:
                vector_dir = self.vault_dir / "vectors"
                self.vector_store = VectorStore(vector_dir, "runes")
                self.hybrid_search = HybridSearch(self.vector_store)
            except Exception as e:
                print(f"Warning: Could not initialize vector store: {e}")
                self.use_vector_search = False

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
                        memory = Memory(**data)
                        self.runes.append(memory)

                        # Add to vector store if enabled
                        if self.use_vector_search:
                            metadata = {
                                'tags': memory.tags,
                                'timestamp': memory.timestamp,
                                'tier': memory.tier
                            }
                            # Use timestamp as ID for consistency
                            doc_id = f"rune_{int(memory.timestamp * 1000000)}"
                            try:
                                self.vector_store.add(memory.text, metadata, doc_id)
                            except Exception:
                                pass  # May already exist

        # Load glyphs
        if self.glyphs_file.exists():
            with open(self.glyphs_file, 'r') as f:
                data = json.load(f)
                self.glyphs = [Memory(**item) for item in data]

        # Load stats
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
                self.reference_counts = Counter(stats.get('reference_counts', {}))

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

    def _save_stats(self) -> None:
        """Persist statistics."""
        with open(self.stats_file, 'w') as f:
            stats = {'reference_counts': dict(self.reference_counts)}
            json.dump(stats, f, indent=2)

    def add_ember(self, text: str, ttl: Optional[float] = 3600) -> str:
        """
        Add short-term memory.

        Args:
            text: Memory text
            ttl: Time to live in seconds

        Returns:
            Memory ID
        """
        ember = Memory(text=text, tier="ember", ttl=ttl)
        self.embers.append(ember)
        self._save_embers()

        # Track for auto-promotion
        text_hash = hash(text)
        self.reference_counts[text_hash] += 1

        # Auto-promote if threshold reached
        if self.reference_counts[text_hash] >= self.auto_promote_threshold:
            print(f"Auto-promoting ember to rune (referenced {self.reference_counts[text_hash]} times)")
            self.add_rune(text, tags=["auto_promoted"])
            del self.reference_counts[text_hash]

        self._save_stats()
        return f"ember_{int(ember.timestamp * 1000000)}"

    def add_rune(self, text: str, tags: Optional[List[str]] = None) -> str:
        """
        Add medium-term memory with vector embedding.

        Args:
            text: Memory text
            tags: Search tags

        Returns:
            Memory ID
        """
        rune = Memory(text=text, tags=tags or [], tier="rune")
        self.runes.append(rune)
        self._save_runes()

        # Add to vector store
        if self.use_vector_search:
            metadata = {
                'tags': rune.tags,
                'timestamp': rune.timestamp,
                'tier': rune.tier
            }
            doc_id = f"rune_{int(rune.timestamp * 1000000)}"
            self.vector_store.add(rune.text, metadata, doc_id)

        return f"rune_{int(rune.timestamp * 1000000)}"

    def add_glyph(self, text: str) -> str:
        """
        Add permanent curated knowledge.

        Args:
            text: Knowledge text

        Returns:
            Memory ID
        """
        glyph = Memory(text=text, tier="glyph")
        self.glyphs.append(glyph)
        self._save_glyphs()
        return f"glyph_{int(glyph.timestamp * 1000000)}"

    def recall(
        self,
        query: str,
        k: int = 8,
        tags: Optional[List[str]] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories using semantic or keyword search.

        Args:
            query: Search query
            k: Number of results
            tags: Filter by tags
            use_semantic: Use semantic search if available

        Returns:
            List of memory dictionaries with scores
        """
        results = []
        current_time = time.time()

        # Search runes with vector search
        if use_semantic and self.use_vector_search:
            # Build metadata filter
            where = None
            if tags:
                where = {"tags": {"$contains": ",".join(tags)}}

            # Use hybrid search
            rune_results = self.hybrid_search.search(
                query,
                n_results=k,
                where=where
            )

            for result in rune_results:
                results.append({
                    'text': result['text'],
                    'score': result['score'],
                    'tier': 'rune',
                    'metadata': result.get('metadata', {}),
                    'id': result['id']
                })

        else:
            # Fallback to keyword search for runes
            for rune in self.runes:
                if tags and not any(tag in rune.tags for tag in tags):
                    continue
                if query.lower() in rune.text.lower():
                    # Simple relevance score based on keyword frequency
                    query_words = query.lower().split()
                    text_lower = rune.text.lower()
                    score = sum(text_lower.count(word) for word in query_words) / len(query_words)

                    results.append({
                        'text': rune.text,
                        'score': score,
                        'tier': 'rune',
                        'metadata': {'tags': rune.tags},
                        'id': f"rune_{int(rune.timestamp * 1000000)}"
                    })

        # Add recent embers (always keyword-based)
        for ember in reversed(self.embers):
            if ember.ttl and (current_time - ember.timestamp) > ember.ttl:
                continue
            if query.lower() in ember.text.lower():
                results.append({
                    'text': ember.text,
                    'score': 0.5,  # Lower score for embers
                    'tier': 'ember',
                    'metadata': {},
                    'id': f"ember_{int(ember.timestamp * 1000000)}"
                })

        # Always include all glyphs
        for glyph in self.glyphs:
            results.append({
                'text': glyph.text,
                'score': 1.0,  # Max score for glyphs
                'tier': 'glyph',
                'metadata': {},
                'id': f"glyph_{int(glyph.timestamp * 1000000)}"
            })

        # Sort by score and return top k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

    def get_recent_embers(self, n: int = 10) -> List[str]:
        """Get N most recent embers."""
        return [e.text for e in list(self.embers)[-n:]]

    def get_glyphs(self) -> List[str]:
        """Get all glyphs."""
        return [g.text for g in self.glyphs]

    def get_runes_by_tags(self, tags: List[str]) -> List[str]:
        """Get runes matching any of the provided tags."""
        results = []
        for rune in self.runes:
            if any(tag in rune.tags for tag in tags):
                results.append(rune.text)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        return {
            'total_embers': len(self.embers),
            'total_runes': len(self.runes),
            'total_glyphs': len(self.glyphs),
            'vector_search_enabled': self.use_vector_search,
            'vector_count': self.vector_store.count() if self.use_vector_search else 0,
            'pending_promotions': len([c for c in self.reference_counts.values() if c >= self.auto_promote_threshold - 1])
        }
