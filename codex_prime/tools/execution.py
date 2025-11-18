"""Tool execution engine with sandboxing and safety."""

import time
import signal
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .registry import ToolRegistry


class TimeoutError(Exception):
    """Raised when tool execution times out."""
    pass


@contextmanager
def timeout(seconds: int):
    """Context manager for execution timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Execution exceeded {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class ToolExecutor:
    """Execute tools with safety controls and logging."""

    def __init__(
        self,
        registry: ToolRegistry,
        default_timeout: int = 30,
        max_retries: int = 0
    ):
        """
        Initialize executor.

        Args:
            registry: Tool registry
            default_timeout: Default execution timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        self.registry = registry
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.execution_log: list[Dict[str, Any]] = []

    def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout_seconds: Optional[int] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with safety controls.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            timeout_seconds: Optional timeout override
            retries: Optional retry count override

        Returns:
            Execution result
        """
        timeout_val = timeout_seconds or self.default_timeout
        retry_count = retries if retries is not None else self.max_retries

        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt <= retry_count:
            try:
                # Execute with timeout
                try:
                    with timeout(timeout_val):
                        result = self.registry.execute(tool_name, **parameters)
                except TimeoutError as e:
                    result = {"success": False, "error": str(e)}

                # Log execution
                elapsed = time.time() - start_time
                log_entry = {
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "attempt": attempt + 1,
                    "elapsed_seconds": elapsed,
                    "timestamp": time.time()
                }
                self.execution_log.append(log_entry)

                # Return on success
                if result.get("success"):
                    return result

                last_error = result.get("error")
                attempt += 1

            except Exception as e:
                last_error = str(e)
                attempt += 1
                if attempt > retry_count:
                    break

                # Wait before retry (exponential backoff)
                time.sleep(min(2 ** attempt, 10))

        # All attempts failed
        return {
            "success": False,
            "error": f"Failed after {attempt} attempts: {last_error}",
            "attempts": attempt
        }

    def execute_chain(
        self,
        tool_chain: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Execute a chain of tools in sequence.

        Args:
            tool_chain: List of dicts with 'tool' and 'parameters' keys

        Returns:
            List of results
        """
        results = []

        for step in tool_chain:
            tool_name = step.get("tool")
            parameters = step.get("parameters", {})

            result = self.execute(tool_name, parameters)
            results.append(result)

            # Stop chain on failure
            if not result.get("success"):
                break

        return results

    def get_execution_log(
        self,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Get execution log.

        Args:
            tool_name: Optional filter by tool name
            limit: Maximum number of entries

        Returns:
            Log entries
        """
        logs = self.execution_log

        if tool_name:
            logs = [log for log in logs if log["tool"] == tool_name]

        return logs[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_log:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "by_tool": {}
            }

        total = len(self.execution_log)
        successes = sum(1 for log in self.execution_log if log["result"].get("success"))

        by_tool = {}
        for log in self.execution_log:
            tool = log["tool"]
            if tool not in by_tool:
                by_tool[tool] = {"total": 0, "successes": 0, "failures": 0}

            by_tool[tool]["total"] += 1
            if log["result"].get("success"):
                by_tool[tool]["successes"] += 1
            else:
                by_tool[tool]["failures"] += 1

        return {
            "total_executions": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "by_tool": by_tool
        }

    def clear_log(self) -> None:
        """Clear execution log."""
        self.execution_log.clear()
