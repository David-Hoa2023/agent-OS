"""Plugin system for Codex Prime.

This module provides a comprehensive plugin architecture that allows
third-party extensions and community contributions.

Key components:
- PluginManager: Install, update, and manage plugins
- PluginLoader: Dynamically load and initialize plugins
- PluginRegistry: Discovery and registration of plugins
- Security scanning and validation
"""

from .schema import (
    PluginManifest,
    PluginType,
    PluginDependency,
    PluginHook,
)
from .manager import PluginManager
from .loader import PluginLoader
from .registry import PluginRegistry
from .security import SecurityScanner

__all__ = [
    "PluginManifest",
    "PluginType",
    "PluginDependency",
    "PluginHook",
    "PluginManager",
    "PluginLoader",
    "PluginRegistry",
    "SecurityScanner",
]
