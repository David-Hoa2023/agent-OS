"""Tool registry for managing available tools."""

from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field

from .base import BaseTool, ToolParameter


@dataclass
class Tool:
    """Simple tool definition using a function."""
    name: str
    description: str
    function: Callable
    parameters: List[ToolParameter] = field(default_factory=list)
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool function."""
        if not self.enabled:
            return {"success": False, "error": "Tool is disabled"}

        try:
            result = self.function(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema."""
        required_params = [p.name for p in self.parameters if p.required]

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: p.to_json_schema()
                    for p in self.parameters
                },
                "required": required_params
            }
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.tags: Dict[str, List[str]] = {}  # tag -> tool names

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

        # Index by tags
        for tag in tool.tags:
            if tag not in self.tags:
                self.tags[tag] = []
            if tool.name not in self.tags[tag]:
                self.tags[tag].append(tool.name)

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self.tools:
            tool = self.tools[name]
            # Remove from tag index
            for tag in tool.tags:
                if tag in self.tags and name in self.tags[tag]:
                    self.tags[tag].remove(name)
            del self.tools[name]

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_all(self) -> List[Tool]:
        """List all tools."""
        return list(self.tools.values())

    def list_enabled(self) -> List[Tool]:
        """List enabled tools."""
        return [t for t in self.tools.values() if t.enabled]

    def list_by_tag(self, tag: str) -> List[Tool]:
        """List tools by tag."""
        tool_names = self.tags.get(tag, [])
        return [self.tools[name] for name in tool_names if name in self.tools]

    def enable(self, name: str) -> None:
        """Enable a tool."""
        if name in self.tools:
            self.tools[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a tool."""
        if name in self.tools:
            self.tools[name].enabled = False

    def to_schemas(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get JSON schemas for tools."""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_schema() for t in tools]

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found"}

        return tool.execute(**kwargs)
