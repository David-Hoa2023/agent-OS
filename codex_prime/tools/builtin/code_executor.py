"""Code execution tools."""

import subprocess
from typing import Optional


class PythonExecutor:
    """Execute Python code in a subprocess."""

    def execute(self, code: str, timeout: int = 5) -> str:
        """
        Execute Python code.

        Args:
            code: Python code to execute
            timeout: Timeout in seconds

        Returns:
            Output from execution
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


class BashExecutor:
    """Execute Bash commands."""

    def __init__(self, allowed_commands: Optional[list[str]] = None):
        """
        Initialize executor.

        Args:
            allowed_commands: Optional whitelist of allowed commands
        """
        self.allowed_commands = allowed_commands

    def execute(self, command: str, timeout: int = 10) -> str:
        """
        Execute bash command.

        Args:
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            Command output
        """
        # Check whitelist if configured
        if self.allowed_commands:
            cmd_name = command.split()[0] if command else ""
            if cmd_name not in self.allowed_commands:
                return f"Error: Command '{cmd_name}' not allowed"

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
