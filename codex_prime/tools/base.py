"""Base classes for tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format."""
        schema = {
            "type": self.type,
            "description": self.description
        }
        if self.default is not None:
            schema["default"] = self.default
        return schema


class BaseTool(ABC):
    """Base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.

        Returns:
            Dictionary with 'success' (bool), 'result' or 'error'
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema for LLM function calling."""
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
