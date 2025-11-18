"""File operation tools."""

from pathlib import Path
from typing import Optional


class FileReader:
    """Read files from disk."""

    def __init__(self, allowed_paths: Optional[list[str]] = None):
        """
        Initialize file reader.

        Args:
            allowed_paths: Optional list of allowed directory paths
        """
        self.allowed_paths = allowed_paths

    def read(self, file_path: str, max_lines: int = 1000) -> str:
        """
        Read file contents.

        Args:
            file_path: Path to file
            max_lines: Maximum number of lines to read

        Returns:
            File contents
        """
        # Check allowed paths
        if self.allowed_paths:
            path = Path(file_path).resolve()
            allowed = any(
                str(path).startswith(str(Path(allowed).resolve()))
                for allowed in self.allowed_paths
            )
            if not allowed:
                return f"Error: Access to {file_path} not allowed"

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()[:max_lines]
                return ''.join(lines)
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileWriter:
    """Write files to disk."""

    def __init__(self, allowed_paths: Optional[list[str]] = None):
        """
        Initialize file writer.

        Args:
            allowed_paths: Optional list of allowed directory paths
        """
        self.allowed_paths = allowed_paths

    def write(self, file_path: str, content: str) -> str:
        """
        Write content to file.

        Args:
            file_path: Path to file
            content: Content to write

        Returns:
            Success message or error
        """
        # Check allowed paths
        if self.allowed_paths:
            path = Path(file_path).resolve()
            allowed = any(
                str(path).startswith(str(Path(allowed).resolve()))
                for allowed in self.allowed_paths
            )
            if not allowed:
                return f"Error: Writing to {file_path} not allowed"

        try:
            # Create parent directories if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                f.write(content)

            return f"Successfully wrote {len(content)} characters to {file_path}"
        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
