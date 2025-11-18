"""Structured logging with JSON format and correlation IDs."""

import logging
import json
import sys
import time
import uuid
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from contextvars import ContextVar

# Context variable for request/correlation ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add correlation ID if present
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)


class StructuredLogger:
    """Structured logger with correlation IDs and context."""

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
        enable_console: bool = True
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            level: Log level
            log_file: Optional file path for logs
            enable_console: Enable console output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Remove existing handlers

        formatter = JSONFormatter()

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with extra fields."""
        extra = kwargs.pop('extra', {})
        extra.update(kwargs)
        self.logger.log(level, message, extra={'extra': extra})

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def set_request_id(self, request_id: Optional[str] = None) -> str:
        """
        Set correlation ID for current context.

        Args:
            request_id: Optional request ID (generated if not provided)

        Returns:
            Request ID
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        return request_id

    def clear_request_id(self):
        """Clear correlation ID from context."""
        request_id_var.set(None)


# Global logger instance
_default_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "codex_prime",
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> StructuredLogger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path

    Returns:
        StructuredLogger instance
    """
    global _default_logger

    if _default_logger is None:
        _default_logger = StructuredLogger(name, level, log_file)

    return _default_logger


class LogContext:
    """Context manager for setting request ID."""

    def __init__(self, logger: StructuredLogger, request_id: Optional[str] = None):
        self.logger = logger
        self.request_id = request_id

    def __enter__(self):
        self.logger.set_request_id(self.request_id)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.clear_request_id()
        return False
