"""Security scanning and validation for plugins."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SecurityIssue:
    """Security issue found during scanning."""

    severity: str  # "critical", "high", "medium", "low"
    category: str
    description: str
    file: str
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "file": self.file,
            "line": self.line
        }


class SecurityScanner:
    """Scans plugins for security vulnerabilities."""

    # Dangerous imports that should be flagged
    DANGEROUS_IMPORTS = {
        "os.system": "critical",
        "subprocess.Popen": "high",
        "eval": "critical",
        "exec": "critical",
        "__import__": "high",
        "compile": "medium",
        "pickle": "medium",
        "marshal": "medium",
        "shelve": "medium",
        "ctypes": "high",
    }

    # Dangerous patterns in code
    DANGEROUS_PATTERNS = [
        (r"os\.system\s*\(", "critical", "Direct system command execution"),
        (r"subprocess\.call\s*\(", "medium", "Subprocess call"),
        (r"eval\s*\(", "critical", "eval() usage"),
        (r"exec\s*\(", "critical", "exec() usage"),
        (r"__import__\s*\(", "high", "Dynamic import"),
        (r"open\s*\([^)]*['\"]w['\"]", "medium", "File write operation"),
        (r"socket\.", "medium", "Network socket usage"),
        (r"requests\.(get|post|put|delete)", "low", "HTTP request"),
    ]

    def __init__(self):
        """Initialize security scanner."""
        self.issues: List[SecurityIssue] = []

    def scan_plugin(self, plugin_path: Path) -> List[SecurityIssue]:
        """Scan a plugin directory for security issues."""
        self.issues = []

        # Scan all Python files
        for py_file in plugin_path.rglob("*.py"):
            self._scan_file(py_file)

        return self.issues

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
                self._scan_ast(tree, file_path)
            except SyntaxError:
                self.issues.append(SecurityIssue(
                    severity="high",
                    category="syntax_error",
                    description="File contains syntax errors",
                    file=str(file_path)
                ))

            # Scan for patterns
            self._scan_patterns(content, file_path)

        except Exception as e:
            self.issues.append(SecurityIssue(
                severity="medium",
                category="scan_error",
                description=f"Failed to scan file: {e}",
                file=str(file_path)
            ))

    def _scan_ast(self, tree: ast.AST, file_path: Path) -> None:
        """Scan AST for dangerous constructs."""
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in self.DANGEROUS_IMPORTS:
                    self.issues.append(SecurityIssue(
                        severity=self.DANGEROUS_IMPORTS[func_name],
                        category="dangerous_function",
                        description=f"Usage of dangerous function: {func_name}",
                        file=str(file_path),
                        line=node.lineno
                    ))

            # Check for dangerous imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_dangerous_module(alias.name):
                        self.issues.append(SecurityIssue(
                            severity="medium",
                            category="dangerous_import",
                            description=f"Import of potentially dangerous module: {alias.name}",
                            file=str(file_path),
                            line=node.lineno
                        ))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}"
                    if full_name in self.DANGEROUS_IMPORTS:
                        self.issues.append(SecurityIssue(
                            severity=self.DANGEROUS_IMPORTS[full_name],
                            category="dangerous_import",
                            description=f"Import of dangerous function: {full_name}",
                            file=str(file_path),
                            line=node.lineno
                        ))

    def _scan_patterns(self, content: str, file_path: Path) -> None:
        """Scan content for dangerous patterns."""
        lines = content.split('\n')

        for pattern, severity, description in self.DANGEROUS_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    self.issues.append(SecurityIssue(
                        severity=severity,
                        category="dangerous_pattern",
                        description=description,
                        file=str(file_path),
                        line=i
                    ))

    @staticmethod
    def _get_function_name(node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = SecurityScanner._get_function_name(node.value)
            return f"{value}.{node.attr}"
        return ""

    @staticmethod
    def _is_dangerous_module(name: str) -> bool:
        """Check if module is potentially dangerous."""
        dangerous_modules = {"ctypes", "subprocess", "pickle", "marshal", "shelve"}
        return name in dangerous_modules

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of security scan."""
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_category = {}

        for issue in self.issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        return {
            "total_issues": len(self.issues),
            "by_severity": by_severity,
            "by_category": by_category,
            "has_critical": by_severity["critical"] > 0,
            "has_high": by_severity["high"] > 0
        }

    def is_safe(self, allow_medium: bool = True, allow_low: bool = True) -> bool:
        """Check if plugin is safe to install."""
        summary = self.get_summary()

        if summary["has_critical"]:
            return False
        if summary["has_high"]:
            return False
        if not allow_medium and summary["by_severity"]["medium"] > 0:
            return False
        if not allow_low and summary["by_severity"]["low"] > 0:
            return False

        return True
