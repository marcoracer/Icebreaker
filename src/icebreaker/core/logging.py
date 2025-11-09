"""Logging configuration for Icebreaker MCP Server.

Structured logging setup following best practices for production environments.
"""

from __future__ import annotations

import structlog
import logging
import sys
from typing import Optional


def configure_logging(
    level: str = "INFO",
    format_json: bool = True,
    enable_colors: bool = False
) -> None:
    """Configure structured logging for Icebreaker.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON format for logs
        enable_colors: Whether to enable colored console output
    """
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add appropriate renderer based on format and color settings
    if format_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        if enable_colors:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=False))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )

    # Make sure structlog's stdlib integration is used
    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=enable_colors) if not format_json else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name or __name__)


class ContextLogger:
    """Context-aware logger for operation tracking.

    Provides automatic context injection for better log analysis.
    """

    def __init__(self, logger_name: str, **context):
        """Initialize context logger.

        Args:
            logger_name: Name of the logger
            **context: Initial context for all log entries
        """
        self.logger = structlog.get_logger(logger_name)
        self.context = context

    def bind(self, **additional_context) -> "ContextLogger":
        """Create a new ContextLogger with additional context.

        Args:
            **additional_context: Additional context to bind

        Returns:
            New ContextLogger instance with merged context
        """
        new_context = {**self.context, **additional_context}
        return ContextLogger(self.logger.name, **new_context)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self.logger.info(message, **{**self.context, **kwargs})

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self.logger.debug(message, **{**self.context, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self.logger.warning(message, **{**self.context, **kwargs})

    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self.logger.error(message, **{**self.context, **kwargs})

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with context."""
        self.logger.critical(message, **{**self.context, **kwargs})


# Default logger instance
default_logger = get_logger(__name__)