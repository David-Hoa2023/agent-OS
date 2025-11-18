"""Plugin manifest schema and validation."""

import re
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import yaml


class PluginType(Enum):
    """Types of plugins supported."""

    TOOL = "tool"
    PROVIDER = "provider"
    MEMORY = "memory"
    COMMAND = "command"
    PERSONA = "persona"


class PluginHook(Enum):
    """Lifecycle hooks for plugins."""

    INIT = "init"
    PRE_CALL = "pre_call"
    POST_CALL = "post_call"
    SHUTDOWN = "shutdown"


@dataclass
class PluginDependency:
    """Plugin dependency specification."""

    name: str
    version: str
    optional: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginDependency":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            version=data.get("version", "*"),
            optional=data.get("optional", False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "optional": self.optional
        }


@dataclass
class PluginManifest:
    """Plugin manifest containing metadata and configuration."""

    # Required fields
    id: str
    name: str
    version: str
    type: PluginType
    entry_point: str
    author: str
    description: str

    # Optional fields
    license: str = "MIT"
    homepage: Optional[str] = None
    repository: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    dependencies: List[PluginDependency] = field(default_factory=list)
    python_requires: str = ">=3.8"
    hooks: List[PluginHook] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate manifest after initialization."""
        # Validate ID format (lowercase, alphanumeric, hyphens)
        if not re.match(r'^[a-z0-9-]+$', self.id):
            raise ValueError(f"Invalid plugin ID: {self.id}. Must be lowercase alphanumeric with hyphens.")

        # Validate version format (semantic versioning)
        if not re.match(r'^\d+\.\d+\.\d+(-[a-z0-9.-]+)?$', self.version):
            raise ValueError(f"Invalid version: {self.version}. Must follow semantic versioning (e.g., 1.0.0).")

        # Convert type to enum if string
        if isinstance(self.type, str):
            self.type = PluginType(self.type)

        # Convert hooks to enum if strings
        if self.hooks and isinstance(self.hooks[0], str):
            self.hooks = [PluginHook(hook) for hook in self.hooks]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create manifest from dictionary."""
        # Parse dependencies
        dependencies = []
        if "dependencies" in data:
            dependencies = [
                PluginDependency.from_dict(dep) if isinstance(dep, dict) else PluginDependency(name=dep, version="*")
                for dep in data["dependencies"]
            ]

        # Parse hooks
        hooks = []
        if "hooks" in data:
            hooks = [PluginHook(hook) for hook in data["hooks"]]

        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            type=PluginType(data["type"]),
            entry_point=data["entry_point"],
            author=data["author"],
            description=data["description"],
            license=data.get("license", "MIT"),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            keywords=data.get("keywords", []),
            dependencies=dependencies,
            python_requires=data.get("python_requires", ">=3.8"),
            hooks=hooks,
            config_schema=data.get("config_schema")
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "PluginManifest":
        """Load manifest from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "entry_point": self.entry_point,
            "author": self.author,
            "description": self.description,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "keywords": self.keywords,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "python_requires": self.python_requires,
            "hooks": [hook.value for hook in self.hooks],
            "config_schema": self.config_schema
        }

    def to_yaml(self, path: Path) -> None:
        """Save manifest to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def is_compatible(self, installed_plugins: Dict[str, "PluginManifest"]) -> tuple[bool, Optional[str]]:
        """Check if plugin is compatible with installed plugins."""
        for dep in self.dependencies:
            if dep.optional:
                continue

            if dep.name not in installed_plugins:
                return False, f"Missing required dependency: {dep.name}"

            installed = installed_plugins[dep.name]
            if not self._version_matches(installed.version, dep.version):
                return False, f"Incompatible version for {dep.name}: required {dep.version}, found {installed.version}"

        return True, None

    @staticmethod
    def _version_matches(installed: str, required: str) -> bool:
        """Check if installed version matches required version constraint."""
        if required == "*":
            return True

        # Simple version matching (can be extended)
        if required.startswith(">="):
            required_version = required[2:].strip()
            return installed >= required_version
        elif required.startswith("=="):
            required_version = required[2:].strip()
            return installed == required_version
        else:
            return installed == required
