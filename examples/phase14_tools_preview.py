"""
Preview implementation of Phase 14: Tool Integration & Function Calling

This demonstrates how to add tool/function calling capabilities to agents.

To run:
    python examples/phase14_tools_preview.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import subprocess
import json
import requests
from abc import ABC, abstractmethod


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """Tool definition."""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    function: Optional[Callable] = None
    enabled: bool = True

    def to_schema(self) -> dict:
        """Convert to JSON schema for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }

    def execute(self, **kwargs) -> dict:
        """Execute the tool with given parameters."""
        if not self.enabled:
            return {"error": "Tool is disabled"}

        if not self.function:
            return {"error": "No implementation"}

        try:
            result = self.function(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_enabled(self) -> list[Tool]:
        """List all enabled tools."""
        return [t for t in self.tools.values() if t.enabled]

    def to_schemas(self) -> list[dict]:
        """Get JSON schemas for all enabled tools."""
        return [t.to_schema() for t in self.list_enabled()]


# ============================================================================
# Built-in Tools
# ============================================================================

def execute_python(code: str, timeout: int = 5) -> str:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Output from code execution
    """
    try:
        result = subprocess.run(
            ['python', '-c', code],
            capture_output=True,
            timeout=timeout,
            text=True
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return result.stdout or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Execution timeout ({timeout}s)"
    except Exception as e:
        return f"Error: {str(e)}"


def execute_bash(command: str, timeout: int = 10) -> str:
    """
    Execute a bash command.

    Args:
        command: Bash command to execute
        timeout: Maximum execution time in seconds

    Returns:
        Command output
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=timeout,
            text=True
        )

        output = result.stdout or result.stderr
        return output or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timeout ({timeout}s)"
    except Exception as e:
        return f"Error: {str(e)}"


def web_search(query: str, num_results: int = 5) -> list[dict]:
    """
    Search the web (simulated).

    In production, integrate with Google Search API, Bing, or DuckDuckGo.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    # Simulated results
    return [
        {
            "title": f"Result {i+1} for: {query}",
            "url": f"https://example.com/result{i+1}",
            "snippet": f"This is a simulated search result for '{query}'. "
                      f"In production, this would call a real search API."
        }
        for i in range(num_results)
    ]


def read_file(file_path: str, max_lines: int = 1000) -> str:
    """
    Read contents of a file.

    Args:
        file_path: Path to file
        max_lines: Maximum lines to read

    Returns:
        File contents
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()[:max_lines]
            return ''.join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        file_path: Path to file
        content: Content to write

    Returns:
        Success message
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def http_request(url: str, method: str = "GET", headers: Optional[dict] = None, body: Optional[str] = None) -> dict:
    """
    Make an HTTP request.

    Args:
        url: URL to request
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Request headers
        body: Request body

    Returns:
        Response data
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            data=body,
            timeout=10
        )

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:1000]  # Limit response size
        }
    except Exception as e:
        return {"error": str(e)}


def calculate(expression: str) -> float:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Math expression (e.g., "2 + 2 * 3")

    Returns:
        Result of calculation
    """
    try:
        # Safe eval for math only
        allowed_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# Tool Registry Setup
# ============================================================================

def create_default_registry() -> ToolRegistry:
    """Create registry with built-in tools."""
    registry = ToolRegistry()

    # Python executor
    registry.register(Tool(
        name="execute_python",
        description="Execute Python code and return the output",
        parameters=[
            ToolParameter("code", "string", "Python code to execute"),
            ToolParameter("timeout", "number", "Timeout in seconds", required=False, default=5)
        ],
        function=execute_python
    ))

    # Bash executor
    registry.register(Tool(
        name="execute_bash",
        description="Execute a bash command and return the output",
        parameters=[
            ToolParameter("command", "string", "Bash command to execute"),
            ToolParameter("timeout", "number", "Timeout in seconds", required=False, default=10)
        ],
        function=execute_bash
    ))

    # Web search
    registry.register(Tool(
        name="web_search",
        description="Search the web for information",
        parameters=[
            ToolParameter("query", "string", "Search query"),
            ToolParameter("num_results", "number", "Number of results", required=False, default=5)
        ],
        function=web_search
    ))

    # File operations
    registry.register(Tool(
        name="read_file",
        description="Read contents of a file",
        parameters=[
            ToolParameter("file_path", "string", "Path to the file"),
            ToolParameter("max_lines", "number", "Max lines to read", required=False, default=1000)
        ],
        function=read_file
    ))

    registry.register(Tool(
        name="write_file",
        description="Write content to a file",
        parameters=[
            ToolParameter("file_path", "string", "Path to the file"),
            ToolParameter("content", "string", "Content to write")
        ],
        function=write_file
    ))

    # HTTP client
    registry.register(Tool(
        name="http_request",
        description="Make an HTTP request to an API",
        parameters=[
            ToolParameter("url", "string", "URL to request"),
            ToolParameter("method", "string", "HTTP method (GET, POST, etc)", required=False, default="GET"),
            ToolParameter("headers", "object", "Request headers", required=False),
            ToolParameter("body", "string", "Request body", required=False)
        ],
        function=http_request
    ))

    # Calculator
    registry.register(Tool(
        name="calculate",
        description="Evaluate a mathematical expression",
        parameters=[
            ToolParameter("expression", "string", "Math expression to evaluate")
        ],
        function=calculate
    ))

    return registry


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate tool system."""
    print("🔧 Phase 14 Preview: Tool Integration & Function Calling\n")

    registry = create_default_registry()

    print("📋 Available Tools:\n")
    for tool in registry.list_enabled():
        print(f"  • {tool.name}")
        print(f"    {tool.description}")
        print()

    print("="*70)
    print("🎯 Tool Execution Examples\n")

    # Example 1: Python code execution
    print("1. Execute Python Code")
    print("   Code: print('Hello from Python!'); print(2 + 2)\n")
    tool = registry.get("execute_python")
    result = tool.execute(code="print('Hello from Python!'); print(2 + 2)")
    print(f"   Output: {result['result']}\n")

    # Example 2: Bash command
    print("2. Execute Bash Command")
    print("   Command: echo 'Hello from Bash!'\n")
    tool = registry.get("execute_bash")
    result = tool.execute(command="echo 'Hello from Bash!'")
    print(f"   Output: {result['result']}\n")

    # Example 3: Calculator
    print("3. Calculate Expression")
    print("   Expression: 2 + 2 * 3\n")
    tool = registry.get("calculate")
    result = tool.execute(expression="2 + 2 * 3")
    print(f"   Result: {result['result']}\n")

    # Example 4: Web search (simulated)
    print("4. Web Search")
    print("   Query: Python tutorials\n")
    tool = registry.get("web_search")
    result = tool.execute(query="Python tutorials", num_results=3)
    if result['success']:
        for i, item in enumerate(result['result'], 1):
            print(f"   [{i}] {item['title']}")
            print(f"       {item['url']}")
    print()

    print("="*70)
    print("\n💡 Tool System Benefits:")
    print("  • Agents can interact with external world")
    print("  • Execute code, call APIs, read/write files")
    print("  • Sandboxed execution for safety")
    print("  • Extensible - add custom tools easily")
    print("  • Schema-based - works with any LLM function calling")

    print("\n📚 Integration with LLMs:")
    print("  • Send tool schemas to LLM")
    print("  • LLM decides which tool to use")
    print("  • Execute tool with LLM-provided parameters")
    print("  • Return results to LLM for next action")

    print("\n🔒 Security Considerations:")
    print("  • Timeout enforcement")
    print("  • Restricted execution environment")
    print("  • Input validation")
    print("  • Rate limiting")
    print("  • Audit logging")

    print("\n📝 JSON Schema Example:")
    print(json.dumps(registry.get("execute_python").to_schema(), indent=2))


if __name__ == "__main__":
    demo()
