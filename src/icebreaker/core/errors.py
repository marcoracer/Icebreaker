"""Icebreaker error classes.

Following the diasv_mcp pattern for clean, HTTP-status-aligned exception hierarchy.
"""

from __future__ import annotations


class IcebreakerError(Exception):
    """Base exception for all Icebreaker errors.

    Controllers may let these propagate; FastMCP will serialize the message.
    Keep messages clear and safe (no sensitive data).
    """


class ValidationError(IcebreakerError):
    """Invalid input provided by the caller (400)."""


class NotFoundError(IcebreakerError):
    """Requested resource does not exist (404)."""


class ConflictError(IcebreakerError):
    """Conflicting state or invariants failed (409)."""


class SafeModeError(IcebreakerError):
    """Operation blocked by safe mode (403)."""


class SnowflakeConnectionError(IcebreakerError):
    """Failed to establish Snowflake connection (503)."""


class PermissionDeniedError(IcebreakerError):
    """Operation not permitted due to insufficient permissions (403)."""


class ConnectionError(IcebreakerError):
    """Failed to establish or maintain connection (503)."""


class ConfigurationError(IcebreakerError):
    """Invalid configuration provided (500)."""