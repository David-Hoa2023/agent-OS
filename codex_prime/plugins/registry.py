"""Plugin discovery and registration."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .schema import PluginManifest, PluginType


logger = logging.getLogger(__name__)


class PluginMetadata:
    """Metadata about an installed plugin."""

    def __init__(
        self,
        manifest: PluginManifest,
        installed_at: datetime,
        install_path: Path,
        enabled: bool = True
    ):
        """Initialize plugin metadata."""
        self.manifest = manifest
        self.installed_at = installed_at
        self.install_path = Path(install_path)
        self.enabled = enabled
        self.last_updated: Optional[datetime] = None
        self.usage_count: int = 0
        self.rating: Optional[float] = None
        self.reviews: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "manifest": self.manifest.to_dict(),
            "installed_at": self.installed_at.isoformat(),
            "install_path": str(self.install_path),
            "enabled": self.enabled,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "reviews": self.reviews
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """Create from dictionary."""
        manifest = PluginManifest.from_dict(data["manifest"])
        metadata = cls(
            manifest=manifest,
            installed_at=datetime.fromisoformat(data["installed_at"]),
            install_path=Path(data["install_path"]),
            enabled=data.get("enabled", True)
        )
        if data.get("last_updated"):
            metadata.last_updated = datetime.fromisoformat(data["last_updated"])
        metadata.usage_count = data.get("usage_count", 0)
        metadata.rating = data.get("rating")
        metadata.reviews = data.get("reviews", [])
        return metadata


class PluginRegistry:
    """Registry for discovering and managing plugins."""

    def __init__(self, registry_file: Path):
        """Initialize plugin registry."""
        self.registry_file = Path(registry_file)
        self.plugins: Dict[str, PluginMetadata] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Load registry from file."""
        if not self.registry_file.exists():
            logger.info("Registry file not found, creating new registry")
            self.plugins = {}
            self.save_registry()
            return

        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)

            self.plugins = {
                plugin_id: PluginMetadata.from_dict(metadata)
                for plugin_id, metadata in data.get("plugins", {}).items()
            }

            logger.info(f"Loaded {len(self.plugins)} plugins from registry")

        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            self.plugins = {}

    def save_registry(self) -> None:
        """Save registry to file."""
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "plugins": {
                    plugin_id: metadata.to_dict()
                    for plugin_id, metadata in self.plugins.items()
                }
            }

            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Registry saved")

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_plugin(
        self,
        manifest: PluginManifest,
        install_path: Path
    ) -> None:
        """Register a new plugin."""
        if manifest.id in self.plugins:
            logger.warning(f"Plugin {manifest.id} already registered, updating")
            self.plugins[manifest.id].manifest = manifest
            self.plugins[manifest.id].last_updated = datetime.now()
        else:
            self.plugins[manifest.id] = PluginMetadata(
                manifest=manifest,
                installed_at=datetime.now(),
                install_path=install_path
            )

        self.save_registry()
        logger.info(f"Registered plugin: {manifest.id} v{manifest.version}")

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin."""
        if plugin_id not in self.plugins:
            logger.warning(f"Plugin {plugin_id} not in registry")
            return

        del self.plugins[plugin_id]
        self.save_registry()
        logger.info(f"Unregistered plugin: {plugin_id}")

    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata."""
        return self.plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, PluginMetadata]:
        """Get all registered plugins."""
        return self.plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginMetadata]:
        """Get all plugins of a specific type."""
        return [
            metadata
            for metadata in self.plugins.values()
            if metadata.manifest.type == plugin_type
        ]

    def search_plugins(
        self,
        query: Optional[str] = None,
        plugin_type: Optional[PluginType] = None,
        keywords: Optional[List[str]] = None,
        enabled_only: bool = False
    ) -> List[PluginMetadata]:
        """Search for plugins."""
        results = list(self.plugins.values())

        # Filter by type
        if plugin_type:
            results = [p for p in results if p.manifest.type == plugin_type]

        # Filter by enabled status
        if enabled_only:
            results = [p for p in results if p.enabled]

        # Filter by keywords
        if keywords:
            results = [
                p for p in results
                if any(kw in p.manifest.keywords for kw in keywords)
            ]

        # Filter by query (search in name, description, keywords)
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p.manifest.name.lower()
                or query_lower in p.manifest.description.lower()
                or any(query_lower in kw.lower() for kw in p.manifest.keywords)
            ]

        # Sort by rating (if available), then by name
        results.sort(key=lambda p: (-(p.rating or 0), p.manifest.name))

        return results

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        self.plugins[plugin_id].enabled = True
        self.save_registry()
        logger.info(f"Enabled plugin: {plugin_id}")

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        self.plugins[plugin_id].enabled = False
        self.save_registry()
        logger.info(f"Disabled plugin: {plugin_id}")

    def increment_usage(self, plugin_id: str) -> None:
        """Increment usage count for a plugin."""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].usage_count += 1
            self.save_registry()

    def add_review(
        self,
        plugin_id: str,
        rating: float,
        comment: str,
        user: str
    ) -> None:
        """Add a review for a plugin."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        review = {
            "rating": rating,
            "comment": comment,
            "user": user,
            "timestamp": datetime.now().isoformat()
        }

        metadata = self.plugins[plugin_id]
        metadata.reviews.append(review)

        # Recalculate average rating
        ratings = [r["rating"] for r in metadata.reviews]
        metadata.rating = sum(ratings) / len(ratings)

        self.save_registry()
        logger.info(f"Added review for plugin {plugin_id}: {rating}/5")

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total = len(self.plugins)
        enabled = sum(1 for p in self.plugins.values() if p.enabled)
        by_type = {}

        for metadata in self.plugins.values():
            plugin_type = metadata.manifest.type.value
            by_type[plugin_type] = by_type.get(plugin_type, 0) + 1

        return {
            "total_plugins": total,
            "enabled_plugins": enabled,
            "disabled_plugins": total - enabled,
            "by_type": by_type,
            "total_usage": sum(p.usage_count for p in self.plugins.values())
        }
