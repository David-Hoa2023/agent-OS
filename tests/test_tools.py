"""Tests for tool system."""

import pytest
import tempfile
from pathlib import Path

from codex_prime.tools.registry import ToolRegistry, Tool, ToolParameter
from codex_prime.tools.execution import ToolExecutor
from codex_prime.tools.builtin import create_default_toolset


def add_numbers(a: int, b: int) -> int:
    """Simple test function."""
    return a + b


def failing_function():
    """Function that always fails."""
    raise ValueError("Intentional failure")


def test_tool_creation():
    """Test creating a tool."""
    tool = Tool(
        name="add",
        description="Add two numbers",
        function=add_numbers,
        parameters=[
            ToolParameter("a", "number", "First number"),
            ToolParameter("b", "number", "Second number")
        ]
    )

    assert tool.name == "add"
    assert len(tool.parameters) == 2


def test_tool_execution():
    """Test executing a tool."""
    tool = Tool(
        name="add",
        description="Add two numbers",
        function=add_numbers,
        parameters=[]
    )

    result = tool.execute(a=2, b=3)

    assert result["success"] == True
    assert result["result"] == 5


def test_tool_execution_failure():
    """Test tool execution failure."""
    tool = Tool(
        name="fail",
        description="Always fails",
        function=failing_function,
        parameters=[]
    )

    result = tool.execute()

    assert result["success"] == False
    assert "error" in result


def test_tool_schema():
    """Test tool JSON schema generation."""
    tool = Tool(
        name="add",
        description="Add two numbers",
        function=add_numbers,
        parameters=[
            ToolParameter("a", "number", "First number"),
            ToolParameter("b", "number", "Second number", required=False, default=0)
        ]
    )

    schema = tool.to_schema()

    assert schema["name"] == "add"
    assert "parameters" in schema
    assert "a" in schema["parameters"]["properties"]
    assert "b" in schema["parameters"]["properties"]
    assert "a" in schema["parameters"]["required"]
    assert "b" not in schema["parameters"]["required"]


def test_registry_register():
    """Test registering tools in registry."""
    registry = ToolRegistry()
    tool = Tool(
        name="test",
        description="Test tool",
        function=lambda: "test",
        tags=["test", "demo"]
    )

    registry.register(tool)

    assert "test" in registry.tools
    assert registry.get("test") == tool


def test_registry_unregister():
    """Test unregistering tools."""
    registry = ToolRegistry()
    tool = Tool(name="test", description="Test", function=lambda: "test")

    registry.register(tool)
    assert "test" in registry.tools

    registry.unregister("test")
    assert "test" not in registry.tools


def test_registry_list_by_tag():
    """Test listing tools by tag."""
    registry = ToolRegistry()

    tool1 = Tool(name="t1", description="Tool 1", function=lambda: 1, tags=["math"])
    tool2 = Tool(name="t2", description="Tool 2", function=lambda: 2, tags=["math", "advanced"])
    tool3 = Tool(name="t3", description="Tool 3", function=lambda: 3, tags=["text"])

    registry.register(tool1)
    registry.register(tool2)
    registry.register(tool3)

    math_tools = registry.list_by_tag("math")
    assert len(math_tools) == 2
    assert all(t.name in ["t1", "t2"] for t in math_tools)


def test_registry_enable_disable():
    """Test enabling and disabling tools."""
    registry = ToolRegistry()
    tool = Tool(name="test", description="Test", function=lambda: "test")

    registry.register(tool)
    assert tool.enabled == True

    registry.disable("test")
    assert registry.get("test").enabled == False

    registry.enable("test")
    assert registry.get("test").enabled == True


def test_registry_execute():
    """Test executing tool through registry."""
    registry = ToolRegistry()
    tool = Tool(
        name="add",
        description="Add numbers",
        function=add_numbers
    )

    registry.register(tool)
    result = registry.execute("add", a=5, b=3)

    assert result["success"] == True
    assert result["result"] == 8


def test_executor_creation():
    """Test creating tool executor."""
    registry = ToolRegistry()
    executor = ToolExecutor(registry)

    assert executor.registry == registry
    assert executor.default_timeout == 30


def test_executor_execute():
    """Test executor executing tools."""
    registry = ToolRegistry()
    tool = Tool(name="add", description="Add", function=add_numbers)
    registry.register(tool)

    executor = ToolExecutor(registry, default_timeout=5)
    result = executor.execute("add", {"a": 10, "b": 20})

    assert result["success"] == True
    assert result["result"] == 30


def test_executor_retry():
    """Test executor retry logic."""
    registry = ToolRegistry()

    call_count = 0

    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"

    tool = Tool(name="flaky", description="Flaky", function=flaky_function)
    registry.register(tool)

    executor = ToolExecutor(registry, max_retries=3)
    result = executor.execute("flaky", {})

    assert result["success"] == True
    assert call_count == 3


def test_executor_stats():
    """Test executor statistics."""
    registry = ToolRegistry()
    tool = Tool(name="add", description="Add", function=add_numbers)
    registry.register(tool)

    executor = ToolExecutor(registry)
    executor.execute("add", {"a": 1, "b": 2})
    executor.execute("add", {"a": 3, "b": 4})

    stats = executor.get_stats()

    assert stats["total_executions"] == 2
    assert stats["success_rate"] == 1.0
    assert "add" in stats["by_tool"]
    assert stats["by_tool"]["add"]["total"] == 2


def test_default_toolset():
    """Test creating default toolset."""
    tools = create_default_toolset()

    assert len(tools) > 0

    tool_names = [t.name for t in tools]
    assert "execute_python" in tool_names
    assert "read_file" in tool_names
    assert "calculate" in tool_names


def test_python_executor_tool():
    """Test Python executor from default toolset."""
    tools = create_default_toolset()
    registry = ToolRegistry()

    for tool in tools:
        registry.register(tool)

    result = registry.execute("execute_python", code="print(2 + 2)")

    assert result["success"] == True
    assert "4" in result["result"]


def test_calculator_tool():
    """Test calculator from default toolset."""
    tools = create_default_toolset()
    registry = ToolRegistry()

    for tool in tools:
        registry.register(tool)

    result = registry.execute("calculate", expression="2 + 2 * 3")

    assert result["success"] == True
    assert result["result"] == 8.0


def test_file_operations():
    """Test file read/write tools."""
    tools = create_default_toolset()
    registry = ToolRegistry()

    for tool in tools:
        registry.register(tool)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        test_file = f.name
        f.write("Test content")

    try:
        # Test read
        result = registry.execute("read_file", file_path=test_file)
        assert result["success"] == True
        assert "Test content" in result["result"]

        # Test write
        new_file = test_file + ".new"
        result = registry.execute("write_file", file_path=new_file, content="New content")
        assert result["success"] == True

        # Verify written content
        result = registry.execute("read_file", file_path=new_file)
        assert "New content" in result["result"]

    finally:
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(new_file):
            os.remove(new_file)
