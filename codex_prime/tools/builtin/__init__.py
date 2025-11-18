"""Built-in tools."""

from .code_executor import PythonExecutor, BashExecutor
from .file_ops import FileReader, FileWriter
from .web_tools import WebSearchTool, HTTPClientTool
from .calculator import Calculator

__all__ = [
    "PythonExecutor",
    "BashExecutor",
    "FileReader",
    "FileWriter",
    "WebSearchTool",
    "HTTPClientTool",
    "Calculator"
]


def create_default_toolset():
    """Create a list of default built-in tools."""
    from ..registry import Tool, ToolParameter

    tools = []

    # Python executor
    python_exec = PythonExecutor()
    tools.append(Tool(
        name="execute_python",
        description="Execute Python code and return the output",
        function=python_exec.execute,
        parameters=[
            ToolParameter("code", "string", "Python code to execute"),
            ToolParameter("timeout", "number", "Timeout in seconds", required=False, default=5)
        ],
        tags=["code", "execution"]
    ))

    # Bash executor
    bash_exec = BashExecutor()
    tools.append(Tool(
        name="execute_bash",
        description="Execute a bash command and return the output",
        function=bash_exec.execute,
        parameters=[
            ToolParameter("command", "string", "Bash command to execute"),
            ToolParameter("timeout", "number", "Timeout in seconds", required=False, default=10)
        ],
        tags=["shell", "execution"]
    ))

    # File reader
    file_reader = FileReader()
    tools.append(Tool(
        name="read_file",
        description="Read contents of a file",
        function=file_reader.read,
        parameters=[
            ToolParameter("file_path", "string", "Path to the file"),
            ToolParameter("max_lines", "number", "Maximum lines to read", required=False, default=1000)
        ],
        tags=["file", "read"]
    ))

    # File writer
    file_writer = FileWriter()
    tools.append(Tool(
        name="write_file",
        description="Write content to a file",
        function=file_writer.write,
        parameters=[
            ToolParameter("file_path", "string", "Path to the file"),
            ToolParameter("content", "string", "Content to write")
        ],
        tags=["file", "write"]
    ))

    # Web search
    web_search = WebSearchTool()
    tools.append(Tool(
        name="web_search",
        description="Search the web for information",
        function=web_search.search,
        parameters=[
            ToolParameter("query", "string", "Search query"),
            ToolParameter("num_results", "number", "Number of results", required=False, default=5)
        ],
        tags=["web", "search"]
    ))

    # HTTP client
    http_client = HTTPClientTool()
    tools.append(Tool(
        name="http_request",
        description="Make an HTTP request to an API",
        function=http_client.request,
        parameters=[
            ToolParameter("url", "string", "URL to request"),
            ToolParameter("method", "string", "HTTP method", required=False, default="GET"),
            ToolParameter("headers", "object", "Request headers", required=False),
            ToolParameter("body", "string", "Request body", required=False)
        ],
        tags=["http", "api"]
    ))

    # Calculator
    calc = Calculator()
    tools.append(Tool(
        name="calculate",
        description="Evaluate a mathematical expression",
        function=calc.calculate,
        parameters=[
            ToolParameter("expression", "string", "Math expression to evaluate")
        ],
        tags=["math", "calculation"]
    ))

    return tools
