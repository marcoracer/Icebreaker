"""Icebreaker MCP Server.

Intelligent Snowflake MCP Agent specialized in DataOps and Administration.
"""

__version__ = "0.1.0"
__author__ = "Icebreaker Team"
__email__ = "team@icebreaker.dev"

from .core.config import IcebreakerConfig
from .core.errors import IcebreakerError, ValidationError, SafeModeError

__all__ = [
    "__version__",
    "IcebreakerConfig",
    "IcebreakerError",
    "ValidationError",
    "SafeModeError",
]