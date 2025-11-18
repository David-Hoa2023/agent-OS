"""Dynamic plugin loading and initialization."""

import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .schema import PluginManifest, PluginHook, PluginType


logger = logging.getLogger(__name__)


class PluginInstance:
    """Represents a loaded plugin instance."""

    def __init__(
        self,
        manifest: PluginManifest,
        module: Any,
        instance: Any
    ):
        """Initialize plugin instance."""
        self.manifest = manifest
        self.module = module
        self.instance = instance
        self.enabled = True

    def call_hook(self, hook: PluginHook, *args, **kwargs) -> Any:
        """Call a lifecycle hook on the plugin."""
        if hook not in self.manifest.hooks:
            return None

        hook_name = hook.value
        if hasattr(self.instance, hook_name):
            method = getattr(self.instance, hook_name)
            try:
                return method(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error calling hook {hook_name} on plugin {self.manifest.id}: {e}")
                raise

        return None

    def get_tool(self):
        """Get tool instance (for TOOL plugins)."""
        if self.manifest.type != PluginType.TOOL:
            raise ValueError(f"Plugin {self.manifest.id} is not a TOOL plugin")
        return self.instance

    def get_provider(self):
        """Get provider instance (for PROVIDER plugins)."""
        if self.manifest.type != PluginType.PROVIDER:
            raise ValueError(f"Plugin {self.manifest.id} is not a PROVIDER plugin")
        return self.instance

    def get_memory_backend(self):
        """Get memory backend instance (for MEMORY plugins)."""
        if self.manifest.type != PluginType.MEMORY:
            raise ValueError(f"Plugin {self.manifest.id} is not a MEMORY plugin")
        return self.instance

    def get_command(self):
        """Get command instance (for COMMAND plugins)."""
        if self.manifest.type != PluginType.COMMAND:
            raise ValueError(f"Plugin {self.manifest.id} is not a COMMAND plugin")
        return self.instance

    def get_persona(self):
        """Get persona data (for PERSONA plugins)."""
        if self.manifest.type != PluginType.PERSONA:
            raise ValueError(f"Plugin {self.manifest.id} is not a PERSONA plugin")
        return self.instance


class PluginLoader:
    """Dynamically loads and manages plugin modules."""

    def __init__(self, plugins_dir: Path):
        """Initialize plugin loader."""
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, PluginInstance] = {}

    def load_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> PluginInstance:
        """Load a plugin by ID."""
        if plugin_id in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} already loaded")
            return self.loaded_plugins[plugin_id]

        # Find plugin directory
        plugin_dir = self.plugins_dir / plugin_id
        if not plugin_dir.exists():
            raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

        # Load manifest
        manifest_path = plugin_dir / "plugin.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin manifest not found: {manifest_path}")

        manifest = PluginManifest.from_yaml(manifest_path)

        # Load module
        entry_point = plugin_dir / manifest.entry_point
        if not entry_point.exists():
            raise FileNotFoundError(f"Plugin entry point not found: {entry_point}")

        module = self._load_module(manifest.id, entry_point)

        # Get plugin class
        plugin_class = self._get_plugin_class(module, manifest)

        # Instantiate plugin
        instance = plugin_class(config or {})

        # Create plugin instance
        plugin_instance = PluginInstance(manifest, module, instance)

        # Call init hook
        plugin_instance.call_hook(PluginHook.INIT)

        # Store loaded plugin
        self.loaded_plugins[plugin_id] = plugin_instance

        logger.info(f"Loaded plugin: {plugin_id} v{manifest.version}")

        return plugin_instance

    def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin."""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return

        plugin = self.loaded_plugins[plugin_id]

        # Call shutdown hook
        try:
            plugin.call_hook(PluginHook.SHUTDOWN)
        except Exception as e:
            logger.error(f"Error during plugin shutdown: {e}")

        # Remove from loaded plugins
        del self.loaded_plugins[plugin_id]

        # Remove module from sys.modules
        if plugin.module.__name__ in sys.modules:
            del sys.modules[plugin.module.__name__]

        logger.info(f"Unloaded plugin: {plugin_id}")

    def reload_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> PluginInstance:
        """Reload a plugin."""
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id, config)

    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """Get a loaded plugin."""
        return self.loaded_plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, PluginInstance]:
        """Get all loaded plugins."""
        return self.loaded_plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInstance]:
        """Get all plugins of a specific type."""
        return [
            plugin
            for plugin in self.loaded_plugins.values()
            if plugin.manifest.type == plugin_type
        ]

    def _load_module(self, plugin_id: str, entry_point: Path) -> Any:
        """Load a Python module from file."""
        spec = importlib.util.spec_from_file_location(plugin_id, entry_point)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load module spec for {entry_point}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_id] = module
        spec.loader.exec_module(module)

        return module

    def _get_plugin_class(self, module: Any, manifest: PluginManifest) -> Any:
        """Extract the plugin class from module."""
        # Look for class name based on convention
        class_names = [
            # Try manifest name converted to class name
            ''.join(word.capitalize() for word in manifest.name.split()),
            # Try common patterns
            f"{manifest.type.value.capitalize()}Plugin",
            "Plugin",
        ]

        for class_name in class_names:
            if hasattr(module, class_name):
                return getattr(module, class_name)

        # If no class found, look for any class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and not attr_name.startswith('_'):
                return attr

        raise ImportError(f"No plugin class found in module {module.__name__}")

    def call_hooks(self, hook: PluginHook, *args, **kwargs) -> Dict[str, Any]:
        """Call a hook on all loaded plugins."""
        results = {}

        for plugin_id, plugin in self.loaded_plugins.items():
            if not plugin.enabled:
                continue

            if hook in plugin.manifest.hooks:
                try:
                    result = plugin.call_hook(hook, *args, **kwargs)
                    results[plugin_id] = result
                except Exception as e:
                    logger.error(f"Error calling hook {hook.value} on plugin {plugin_id}: {e}")
                    results[plugin_id] = {"error": str(e)}

        return results
