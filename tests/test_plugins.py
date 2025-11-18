"""Tests for plugin system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from codex_prime.plugins import (
    PluginManifest,
    PluginType,
    PluginDependency,
    PluginHook,
    PluginManager,
    PluginLoader,
    PluginRegistry,
    SecurityScanner,
)


# Plugin Manifest Tests

def test_plugin_manifest_creation():
    """Test creating a plugin manifest."""
    manifest = PluginManifest(
        id="test-plugin",
        name="Test Plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="main.py",
        author="Test Author",
        description="A test plugin"
    )

    assert manifest.id == "test-plugin"
    assert manifest.name == "Test Plugin"
    assert manifest.version == "1.0.0"
    assert manifest.type == PluginType.TOOL
    assert manifest.entry_point == "main.py"


def test_plugin_manifest_validation():
    """Test manifest validation."""
    # Invalid ID (uppercase)
    with pytest.raises(ValueError, match="Invalid plugin ID"):
        PluginManifest(
            id="TestPlugin",
            name="Test",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="main.py",
            author="Author",
            description="Test"
        )

    # Invalid version
    with pytest.raises(ValueError, match="Invalid version"):
        PluginManifest(
            id="test-plugin",
            name="Test",
            version="1.0",
            type=PluginType.TOOL,
            entry_point="main.py",
            author="Author",
            description="Test"
        )


def test_plugin_manifest_serialization():
    """Test manifest serialization."""
    manifest = PluginManifest(
        id="test-plugin",
        name="Test Plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="main.py",
        author="Test Author",
        description="A test plugin",
        keywords=["test", "example"],
        hooks=[PluginHook.INIT, PluginHook.SHUTDOWN]
    )

    # To dict
    data = manifest.to_dict()
    assert data["id"] == "test-plugin"
    assert data["type"] == "tool"
    assert "init" in data["hooks"]

    # From dict
    manifest2 = PluginManifest.from_dict(data)
    assert manifest2.id == manifest.id
    assert manifest2.type == manifest.type
    assert manifest2.hooks == manifest.hooks


def test_plugin_dependency():
    """Test plugin dependencies."""
    dep = PluginDependency(
        name="other-plugin",
        version=">=1.0.0",
        optional=False
    )

    assert dep.name == "other-plugin"
    assert dep.version == ">=1.0.0"
    assert not dep.optional

    # Serialization
    data = dep.to_dict()
    dep2 = PluginDependency.from_dict(data)
    assert dep2.name == dep.name


def test_plugin_compatibility():
    """Test plugin compatibility checking."""
    manifest = PluginManifest(
        id="test-plugin",
        name="Test",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="main.py",
        author="Author",
        description="Test",
        dependencies=[
            PluginDependency("dep1", ">=1.0.0"),
            PluginDependency("dep2", "*", optional=True)
        ]
    )

    # Missing required dependency
    compatible, error = manifest.is_compatible({})
    assert not compatible
    assert "dep1" in error

    # Has required dependency
    dep1_manifest = PluginManifest(
        id="dep1",
        name="Dep1",
        version="1.5.0",
        type=PluginType.TOOL,
        entry_point="main.py",
        author="Author",
        description="Dependency"
    )

    compatible, error = manifest.is_compatible({"dep1": dep1_manifest})
    assert compatible
    assert error is None


# Security Scanner Tests

def test_security_scanner_creation():
    """Test creating a security scanner."""
    scanner = SecurityScanner()
    assert scanner.issues == []


def test_security_scanner_dangerous_patterns():
    """Test detection of dangerous patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)

        # Create a file with dangerous code
        test_file = plugin_dir / "test.py"
        test_file.write_text("""
import os

def dangerous_function():
    os.system("rm -rf /")
    eval("print('hello')")
""")

        scanner = SecurityScanner()
        issues = scanner.scan_plugin(plugin_dir)

        assert len(issues) > 0
        assert any(issue.severity in ["critical", "high"] for issue in issues)
        assert not scanner.is_safe()


def test_security_scanner_safe_code():
    """Test scanning safe code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)

        # Create a safe file
        test_file = plugin_dir / "test.py"
        test_file.write_text("""
def safe_function():
    return "Hello, world!"

class SafeClass:
    def __init__(self):
        self.value = 42
""")

        scanner = SecurityScanner()
        issues = scanner.scan_plugin(plugin_dir)

        # Should have no critical or high severity issues
        summary = scanner.get_summary()
        assert summary["has_critical"] == False
        assert scanner.is_safe()


# Plugin Registry Tests

def test_plugin_registry_creation():
    """Test creating a plugin registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_file = Path(tmpdir) / "registry.json"
        registry = PluginRegistry(registry_file)

        assert registry.plugins == {}


def test_plugin_registry_register():
    """Test registering plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_file = Path(tmpdir) / "registry.json"
        registry = PluginRegistry(registry_file)

        manifest = PluginManifest(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="main.py",
            author="Author",
            description="Test"
        )

        registry.register_plugin(manifest, Path(tmpdir) / "plugin")

        assert "test-plugin" in registry.plugins
        assert registry.plugins["test-plugin"].manifest.id == "test-plugin"


def test_plugin_registry_persistence():
    """Test registry persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_file = Path(tmpdir) / "registry.json"

        # Create and save registry
        registry1 = PluginRegistry(registry_file)

        manifest = PluginManifest(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="main.py",
            author="Author",
            description="Test"
        )

        registry1.register_plugin(manifest, Path(tmpdir) / "plugin")

        # Load in new instance
        registry2 = PluginRegistry(registry_file)
        assert "test-plugin" in registry2.plugins


def test_plugin_registry_search():
    """Test searching plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_file = Path(tmpdir) / "registry.json"
        registry = PluginRegistry(registry_file)

        # Register multiple plugins
        for i in range(3):
            manifest = PluginManifest(
                id=f"plugin-{i}",
                name=f"Plugin {i}",
                version="1.0.0",
                type=PluginType.TOOL if i % 2 == 0 else PluginType.PROVIDER,
                entry_point="main.py",
                author="Author",
                description=f"Test plugin {i}",
                keywords=["test", f"keyword{i}"]
            )
            registry.register_plugin(manifest, Path(tmpdir) / f"plugin-{i}")

        # Search by query
        results = registry.search_plugins(query="Plugin 1")
        assert len(results) == 1
        assert results[0].manifest.id == "plugin-1"

        # Search by type
        results = registry.search_plugins(plugin_type=PluginType.TOOL)
        assert all(p.manifest.type == PluginType.TOOL for p in results)


def test_plugin_registry_enable_disable():
    """Test enabling/disabling plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_file = Path(tmpdir) / "registry.json"
        registry = PluginRegistry(registry_file)

        manifest = PluginManifest(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="main.py",
            author="Author",
            description="Test"
        )

        registry.register_plugin(manifest, Path(tmpdir) / "plugin")

        # Should be enabled by default
        assert registry.plugins["test-plugin"].enabled

        # Disable
        registry.disable_plugin("test-plugin")
        assert not registry.plugins["test-plugin"].enabled

        # Enable
        registry.enable_plugin("test-plugin")
        assert registry.plugins["test-plugin"].enabled


# Plugin Loader Tests

def test_plugin_loader_creation():
    """Test creating a plugin loader."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = PluginLoader(Path(tmpdir))
        assert loader.loaded_plugins == {}


def test_plugin_loader_load_plugin():
    """Test loading a plugin."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        # Create a simple plugin
        plugin_dir = plugins_dir / "test-plugin"
        plugin_dir.mkdir()

        # Create manifest
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="plugin.py",
            author="Test Author",
            description="A test plugin",
            hooks=[PluginHook.INIT]
        )
        manifest.to_yaml(plugin_dir / "plugin.yaml")

        # Create plugin code
        plugin_code = '''
class TestPlugin:
    def __init__(self, config):
        self.config = config

    def init(self):
        print("Plugin initialized")

    def get_name(self):
        return "test"
'''
        (plugin_dir / "plugin.py").write_text(plugin_code)

        # Load plugin
        loader = PluginLoader(plugins_dir)
        instance = loader.load_plugin("test-plugin")

        assert instance is not None
        assert instance.manifest.id == "test-plugin"
        assert "test-plugin" in loader.loaded_plugins


def test_plugin_loader_unload_plugin():
    """Test unloading a plugin."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        # Create and load plugin
        plugin_dir = plugins_dir / "test-plugin"
        plugin_dir.mkdir()

        manifest = PluginManifest(
            id="test-plugin",
            name="Test",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="plugin.py",
            author="Author",
            description="Test",
            hooks=[PluginHook.SHUTDOWN]
        )
        manifest.to_yaml(plugin_dir / "plugin.yaml")

        plugin_code = '''
class Plugin:
    def __init__(self, config):
        pass

    def shutdown(self):
        print("Shutting down")
'''
        (plugin_dir / "plugin.py").write_text(plugin_code)

        loader = PluginLoader(plugins_dir)
        loader.load_plugin("test-plugin")

        assert "test-plugin" in loader.loaded_plugins

        # Unload
        loader.unload_plugin("test-plugin")
        assert "test-plugin" not in loader.loaded_plugins


# Plugin Manager Tests

def test_plugin_manager_creation():
    """Test creating a plugin manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir) / "plugins"
        registry_file = Path(tmpdir) / "registry.json"

        manager = PluginManager(plugins_dir, registry_file)

        assert manager.plugins_dir.exists()
        assert isinstance(manager.registry, PluginRegistry)
        assert isinstance(manager.loader, PluginLoader)


def test_plugin_manager_install():
    """Test installing a plugin."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup manager
        plugins_dir = Path(tmpdir) / "plugins"
        registry_file = Path(tmpdir) / "registry.json"
        manager = PluginManager(plugins_dir, registry_file, auto_scan_security=False)

        # Create plugin to install
        source_dir = Path(tmpdir) / "source" / "test-plugin"
        source_dir.mkdir(parents=True)

        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="plugin.py",
            author="Test Author",
            description="A test plugin"
        )
        manifest.to_yaml(source_dir / "plugin.yaml")

        plugin_code = '''
class Plugin:
    def __init__(self, config):
        self.config = config
'''
        (source_dir / "plugin.py").write_text(plugin_code)

        # Install
        installed_manifest = manager.install_plugin(source_dir)

        assert installed_manifest.id == "test-plugin"
        assert (plugins_dir / "test-plugin").exists()
        assert "test-plugin" in manager.registry.plugins


def test_plugin_manager_list():
    """Test listing plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir) / "plugins"
        registry_file = Path(tmpdir) / "registry.json"
        manager = PluginManager(plugins_dir, registry_file, auto_scan_security=False)

        # Create and install plugin
        source_dir = Path(tmpdir) / "source" / "test-plugin"
        source_dir.mkdir(parents=True)

        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="plugin.py",
            author="Test Author",
            description="A test plugin"
        )
        manifest.to_yaml(source_dir / "plugin.yaml")
        (source_dir / "plugin.py").write_text("class Plugin:\n    def __init__(self, config): pass")

        manager.install_plugin(source_dir)

        # List plugins
        plugins = manager.list_plugins()

        assert len(plugins) == 1
        assert plugins[0]["id"] == "test-plugin"
        assert plugins[0]["name"] == "Test Plugin"


def test_plugin_manager_stats():
    """Test plugin statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir) / "plugins"
        registry_file = Path(tmpdir) / "registry.json"
        manager = PluginManager(plugins_dir, registry_file)

        stats = manager.get_stats()

        assert "total_plugins" in stats
        assert "enabled_plugins" in stats
        assert "loaded_plugins" in stats
        assert "by_type" in stats
