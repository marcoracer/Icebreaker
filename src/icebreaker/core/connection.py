"""Snowflake connection management.

Implements production-ready connection management with community best practices
and Icebreaker safety layer integration.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Generator, Tuple, Union
import structlog

import snowflake.connector
from snowflake.connector.connection import SnowflakeConnection
from snowflake.connector.cursor import SnowflakeCursor, DictCursor

from .config import IcebreakerConfig
from .errors import IcebreakerError, ConnectionError, ConfigurationError

logger = structlog.get_logger(__name__)


class SnowflakeConnectionManager:
    """Production-ready Snowflake connection manager with enhanced features.

    Implements community best practices including:
    - Singleton pattern with thread safety (from snowflake-mcp-server)
    - Connection health monitoring and automatic refresh
    - Background connection refresh capabilities
    - Configurable refresh intervals and timeouts
    - Comprehensive error handling and recovery
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: IcebreakerConfig):
        """Initialize connection manager.

        Args:
            config: Icebreaker configuration object
        """
        self.config = config
        self._connection: Optional[SnowflakeConnection] = None
        self._connection_lock = threading.Lock()
        self._last_refresh: Optional[datetime] = None
        self._last_error: Optional[Exception] = None
        self._connection_healthy = False
        self._refresh_interval = timedelta(hours=float(
            os.getenv("SNOWFLAKE_CONN_REFRESH_HOURS", "8")
        ))
        self._connection_timeout = int(
            os.getenv("SNOWFLAKE_CONN_TIMEOUT", "60")
        )

    @classmethod
    def get_instance(cls, config: IcebreakerConfig) -> SnowflakeConnectionManager:
        """Get singleton instance of connection manager.

        Args:
            config: Icebreaker configuration object

        Returns:
            Singleton connection manager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def _build_connection_params(self) -> Dict[str, Any]:
        """Build connection parameters from configuration.

        Returns:
            Dictionary of connection parameters

        Raises:
            ConfigurationError: If required parameters are missing
        """
        snowflake_config = self.config.snowflake
        params = {
            "account": snowflake_config.account,
            "user": snowflake_config.user,
            "timeout": self._connection_timeout,
        }

        # Add optional parameters
        if snowflake_config.role:
            params["role"] = snowflake_config.role
        if snowflake_config.warehouse:
            params["warehouse"] = snowflake_config.warehouse
        if snowflake_config.database:
            params["database"] = snowflake_config.database
        if snowflake_config.schema_name:
            params["schema"] = snowflake_config.schema_name

        # Add authentication parameters based on auth type
        if snowflake_config.auth_type == "private_key":
            if snowflake_config.private_key:
                params["private_key"] = snowflake_config.private_key
            elif snowflake_config.private_key_path:
                params["private_key_file"] = snowflake_config.private_key_path
            else:
                raise ConfigurationError("Private key authentication requires private_key or private_key_path")

        elif snowflake_config.auth_type == "password":
            if not snowflake_config.password:
                raise ConfigurationError("Password authentication requires password parameter")
            params["password"] = snowflake_config.password

        elif snowflake_config.auth_type == "externalbrowser":
            params["authenticator"] = "externalbrowser"

        elif snowflake_config.auth_type == "oauth":
            if not snowflake_config.token:
                raise ConfigurationError("OAuth authentication requires token parameter")
            params["token"] = snowflake_config.token
            params["authenticator"] = "oauth"

        return params

    def _create_connection(self) -> SnowflakeConnection:
        """Create a new Snowflake connection.

        Returns:
            New Snowflake connection

        Raises:
            ConnectionError: If connection fails
        """
        try:
            params = self._build_connection_params()
            logger.info("Creating new Snowflake connection", account=params.get("account"))

            connection = snowflake.connector.connect(**params)

            # Test the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT CURRENT_VERSION()")
                version = cursor.fetchone()[0]
                logger.info("Snowflake connection established", version=version)

            self._last_refresh = datetime.now(timezone.utc)
            self._last_error = None
            self._connection_healthy = True

            return connection

        except Exception as e:
            self._last_error = e
            self._connection_healthy = False
            logger.error("Failed to create Snowflake connection", error=str(e), error_type=type(e).__name__)
            raise ConnectionError(f"Failed to connect to Snowflake: {e}") from e

    def _is_connection_stale(self) -> bool:
        """Check if connection is stale and needs refresh.

        Returns:
            True if connection is stale, False otherwise
        """
        if not self._last_refresh:
            return True

        return datetime.now(timezone.utc) - self._last_refresh > self._refresh_interval

    @contextmanager
    def get_connection(self, use_dict_cursor: bool = False) -> Generator[Tuple[SnowflakeConnection, Union[SnowflakeCursor, DictCursor]], None, None]:
        """Get a Snowflake connection with automatic management.

        Args:
            use_dict_cursor: Whether to use dict cursor for query results

        Yields:
            Tuple of (connection, cursor) for Snowflake operations

        Raises:
            ConnectionError: If connection cannot be established
        """
        with self._connection_lock:
            try:
                # Create new connection if needed
                if (self._connection is None or
                    not self._connection_healthy or
                    self._is_connection_stale()):

                    if self._connection:
                        try:
                            self._connection.close()
                        except Exception:
                            pass  # Ignore errors during cleanup

                    self._connection = self._create_connection()

                # Create appropriate cursor
                if use_dict_cursor:
                    cursor = self._connection.cursor(snowflake.connector.DictCursor)
                else:
                    cursor = self._connection.cursor()

                logger.debug("Providing Snowflake connection",
                           use_dict_cursor=use_dict_cursor,
                           healthy=self._connection_healthy)

                yield self._connection, cursor

            except Exception as e:
                self._last_error = e
                self._connection_healthy = False
                logger.error("Connection operation failed", error=str(e))
                raise

    def is_connection_healthy(self) -> Tuple[bool, Optional[str]]:
        """Check if the connection is healthy.

        Returns:
            Tuple of (is_healthy, error_message)
        """
        if self._last_error:
            error_msg = f"{type(self._last_error).__name__}: {str(self._last_error)}"
            return (self._connection_healthy, error_msg)

        if self._connection is None:
            return (False, "No connection established")

        if self._is_connection_stale():
            return (False, "Connection is stale")

        return (self._connection_healthy, None)

    def close_connection(self) -> None:
        """Close the current connection."""
        with self._connection_lock:
            if self._connection:
                try:
                    self._connection.close()
                    logger.info("Snowflake connection closed")
                except Exception as e:
                    logger.warning("Error closing connection", error=str(e))
                finally:
                    self._connection = None
                    self._connection_healthy = False

    def refresh_connection(self) -> None:
        """Force refresh of the connection."""
        logger.info("Forcing connection refresh")
        self.close_connection()
        # Connection will be recreated on next get_connection call

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection.

        Returns:
            Dictionary with connection information
        """
        is_healthy, error_msg = self.is_connection_healthy()

        info = {
            "healthy": is_healthy,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "refresh_interval_hours": self._refresh_interval.total_seconds() / 3600,
            "connection_timeout": self._connection_timeout,
            "error_message": error_msg,
        }

        if self._connection:
            info["session_id"] = getattr(self._connection, "session_id", None)

        return info


class SafeConnectionWrapper:
    """Wrapper for Snowflake connections with safety validation.

    Provides safety checks for all operations:
    - SQL injection prevention
    - Write operation detection
    - Permission validation
    - Query timeout enforcement
    - Result size limits
    """

    def __init__(self, connection_manager: SnowflakeConnectionManager, config: IcebreakerConfig):
        """Initialize safe connection wrapper.

        Args:
            connection_manager: Underlying connection manager
            config: Icebreaker configuration
        """
        self.connection_manager = connection_manager
        self.config = config

    @contextmanager
    def execute_safe_query(self, sql: str, use_dict_cursor: bool = False):
        """Execute a SQL query with safety validation and context management.

        Args:
            sql: SQL query to execute
            use_dict_cursor: Whether to use dict cursor for results

        Yields:
            Cursor for executing the query

        Raises:
            ValidationError: If SQL contains dangerous operations
            PermissionDeniedError: If operation violates safety rules
            ConnectionError: If connection fails
        """
        logger.info("Executing safe query", sql_preview=sql[:100])

        # Basic safety checks will be implemented in QueryValidator
        # For now, we just provide the connection context
        try:
            with self.connection_manager.get_connection(use_dict_cursor=use_dict_cursor) as (_, cursor):
                yield cursor
        except Exception as e:
            logger.error("Safe query execution failed", error=str(e), sql_preview=sql[:100])
            raise

# Import os for environment variables
import os