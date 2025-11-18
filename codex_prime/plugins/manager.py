"""Plugin lifecycle management."""

import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json

from .schema import PluginManifest, PluginType
from .loader import PluginLoader, PluginInstance
from .registry import PluginRegistry
from .security import SecurityScanner


logger = logging.getLogger(__name__)


class PluginManager:
    """Manages the complete plugin lifecycle."""

    def __init__(
        self,
        plugins_dir: Path,
        registry_file: Path,
        auto_scan_security: bool = True
    ):
        """Initialize plugin manager."""
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.registry = PluginRegistry(registry_file)
        self.loader = PluginLoader(self.plugins_dir)
        self.auto_scan_security = auto_scan_security

    def install_plugin(
        self,
        source: Path,
        force: bool = False
    ) -> PluginManifest:
        """Install a plugin from a directory or ZIP file.

        Args:
            source: Path to plugin directory or ZIP file
            force: Install even if security issues are found

        Returns:
            PluginManifest of installed plugin

        Raises:
            ValueError: If plugin is invalid or unsafe
            FileNotFoundError: If source not found
        """
        source = Path(source)

        if not source.exists():
            raise FileNotFoundError(f"Plugin source not found: {source}")

        # Extract if ZIP
        if source.is_file() and source.suffix == '.zip':
            temp_dir = self.plugins_dir / "__temp__"
            temp_dir.mkdir(exist_ok=True)

            try:
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find plugin directory (should contain plugin.yaml)
                plugin_dirs = list(temp_dir.glob("**/plugin.yaml"))
                if not plugin_dirs:
                    raise ValueError("No plugin.yaml found in ZIP file")

                source = plugin_dirs[0].parent

            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise ValueError(f"Failed to extract ZIP file: {e}")

        # Load manifest
        manifest_path = source / "plugin.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"plugin.yaml not found in {source}")

        manifest = PluginManifest.from_yaml(manifest_path)

        # Check if already installed
        existing = self.registry.get_plugin(manifest.id)
        if existing and not force:
            raise ValueError(
                f"Plugin {manifest.id} already installed (version {existing.manifest.version}). "
                f"Use update_plugin() or force=True to overwrite."
            )

        # Security scan
        if self.auto_scan_security:
            scanner = SecurityScanner()
            issues = scanner.scan_plugin(source)

            if issues and not force:
                summary = scanner.get_summary()
                if summary["has_critical"] or summary["has_high"]:
                    raise ValueError(
                        f"Security issues found in plugin {manifest.id}:\n"
                        f"  Critical: {summary['by_severity']['critical']}\n"
                        f"  High: {summary['by_severity']['high']}\n"
                        f"Use force=True to install anyway (not recommended)"
                    )

            logger.info(f"Security scan completed: {len(issues)} issues found")

        # Check dependencies
        installed_plugins = {
            pid: meta.manifest
            for pid, meta in self.registry.get_all_plugins().items()
        }

        compatible, error = manifest.is_compatible(installed_plugins)
        if not compatible:
            raise ValueError(f"Plugin not compatible: {error}")

        # Install to plugins directory
        install_path = self.plugins_dir / manifest.id

        # Remove old version if exists
        if install_path.exists():
            shutil.rmtree(install_path)

        # Copy plugin files
        shutil.copytree(source, install_path)

        # Clean up temp directory if used
        temp_dir = self.plugins_dir / "__temp__"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Register plugin
        self.registry.register_plugin(manifest, install_path)

        logger.info(f"Installed plugin: {manifest.id} v{manifest.version}")

        return manifest

    def uninstall_plugin(self, plugin_id: str) -> None:
        """Uninstall a plugin."""
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Unload if loaded
        if self.loader.get_plugin(plugin_id):
            self.loader.unload_plugin(plugin_id)

        # Remove files
        install_path = metadata.install_path
        if install_path.exists():
            shutil.rmtree(install_path)

        # Unregister
        self.registry.unregister_plugin(plugin_id)

        logger.info(f"Uninstalled plugin: {plugin_id}")

    def update_plugin(self, source: Path) -> PluginManifest:
        """Update an installed plugin."""
        source = Path(source)

        # Load new manifest
        if source.is_dir():
            manifest_path = source / "plugin.yaml"
        else:
            # For ZIP files, we need to extract temporarily
            temp_dir = self.plugins_dir / "__temp_update__"
            temp_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(source, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            plugin_dirs = list(temp_dir.glob("**/plugin.yaml"))
            if not plugin_dirs:
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise ValueError("No plugin.yaml found in ZIP file")

            manifest_path = plugin_dirs[0]

        new_manifest = PluginManifest.from_yaml(manifest_path)

        # Check if plugin is installed
        existing = self.registry.get_plugin(new_manifest.id)
        if not existing:
            raise ValueError(f"Plugin {new_manifest.id} not installed. Use install_plugin() instead.")

        # Check version
        if new_manifest.version <= existing.manifest.version:
            logger.warning(
                f"New version {new_manifest.version} is not newer than "
                f"installed version {existing.manifest.version}"
            )

        # Install with force=True to overwrite
        manifest = self.install_plugin(source, force=True)

        # Clean up temp
        temp_dir = self.plugins_dir / "__temp_update__"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.info(f"Updated plugin: {manifest.id} to v{manifest.version}")

        return manifest

    def load_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> PluginInstance:
        """Load a plugin into memory."""
        # Check if registered
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise ValueError(f"Plugin {plugin_id} not registered")

        if not metadata.enabled:
            raise ValueError(f"Plugin {plugin_id} is disabled")

        # Load plugin
        instance = self.loader.load_plugin(plugin_id, config)

        # Increment usage count
        self.registry.increment_usage(plugin_id)

        return instance

    def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin from memory."""
        self.loader.unload_plugin(plugin_id)

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin."""
        self.registry.enable_plugin(plugin_id)

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin."""
        # Unload if loaded
        if self.loader.get_plugin(plugin_id):
            self.loader.unload_plugin(plugin_id)

        self.registry.disable_plugin(plugin_id)

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List installed plugins."""
        if plugin_type:
            plugins = self.registry.get_plugins_by_type(plugin_type)
        else:
            plugins = list(self.registry.get_all_plugins().values())

        if enabled_only:
            plugins = [p for p in plugins if p.enabled]

        return [
            {
                "id": p.manifest.id,
                "name": p.manifest.name,
                "version": p.manifest.version,
                "type": p.manifest.type.value,
                "author": p.manifest.author,
                "description": p.manifest.description,
                "enabled": p.enabled,
                "installed_at": p.installed_at.isoformat(),
                "usage_count": p.usage_count,
                "rating": p.rating,
                "loaded": p.manifest.id in self.loader.loaded_plugins
            }
            for p in plugins
        ]

    def search_plugins(
        self,
        query: str,
        plugin_type: Optional[PluginType] = None
    ) -> List[Dict[str, Any]]:
        """Search for plugins."""
        results = self.registry.search_plugins(
            query=query,
            plugin_type=plugin_type
        )

        return [
            {
                "id": p.manifest.id,
                "name": p.manifest.name,
                "version": p.manifest.version,
                "type": p.manifest.type.value,
                "description": p.manifest.description,
                "rating": p.rating
            }
            for p in results
        ]

    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed information about a plugin."""
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise ValueError(f"Plugin {plugin_id} not found")

        instance = self.loader.get_plugin(plugin_id)

        return {
            "manifest": metadata.manifest.to_dict(),
            "enabled": metadata.enabled,
            "installed_at": metadata.installed_at.isoformat(),
            "last_updated": metadata.last_updated.isoformat() if metadata.last_updated else None,
            "usage_count": metadata.usage_count,
            "rating": metadata.rating,
            "reviews": metadata.reviews,
            "loaded": instance is not None,
            "install_path": str(metadata.install_path)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        registry_stats = self.registry.get_stats()
        loaded_plugins = len(self.loader.loaded_plugins)

        return {
            **registry_stats,
            "loaded_plugins": loaded_plugins,
            "plugins_dir": str(self.plugins_dir)
        }

    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for plugin updates (placeholder for marketplace integration)."""
        # This would connect to a marketplace API in a real implementation
        logger.info("Checking for plugin updates...")
        return []

    def export_plugin(self, plugin_id: str, output_path: Path) -> None:
        """Export a plugin to a ZIP file."""
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise ValueError(f"Plugin {plugin_id} not found")

        output_path = Path(output_path)

        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            plugin_dir = metadata.install_path

            for file_path in plugin_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(plugin_dir.parent)
                    zipf.write(file_path, arcname)

        logger.info(f"Exported plugin {plugin_id} to {output_path}")
