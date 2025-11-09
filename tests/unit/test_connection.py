"""Unit tests for Snowflake connection management."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock, call, MagicMock
from contextlib import contextmanager

import pytest
import snowflake.connector
from snowflake.connector.connection import SnowflakeConnection
from snowflake.connector.cursor import SnowflakeCursor, DictCursor

from icebreaker.core.config import IcebreakerConfig, SnowflakeConfig, AuthType
from icebreaker.core.connection import SnowflakeConnectionManager, SafeConnectionWrapper
from icebreaker.core.errors import ConnectionError, ConfigurationError


class TestSnowflakeConnectionManager:
    """Test cases for SnowflakeConnectionManager."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Icebreaker configuration for testing."""
        snowflake_config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            auth_type=AuthType.PASSWORD,
            password="test_password",
            role="test_role",
            warehouse="test_warehouse",
            database="test_db",
            schema_name="test_schema"
        )
        config = Mock(spec=IcebreakerConfig)
        config.snowflake = snowflake_config
        config.safe_mode = True
        return config

    @pytest.fixture
    def connection_manager(self, mock_config):
        """Create a connection manager instance for testing."""
        # Reset singleton for each test
        SnowflakeConnectionManager._instance = None
        return SnowflakeConnectionManager(mock_config)

    def test_init(self, connection_manager, mock_config):
        """Test connection manager initialization."""
        assert connection_manager.config == mock_config
        assert connection_manager._connection is None
        assert connection_manager._connection_healthy is False
        assert connection_manager._last_refresh is None
        assert connection_manager._last_error is None

    def test_singleton_pattern(self, mock_config):
        """Test that connection manager follows singleton pattern."""
        # Reset singleton
        SnowflakeConnectionManager._instance = None

        manager1 = SnowflakeConnectionManager.get_instance(mock_config)
        manager2 = SnowflakeConnectionManager.get_instance(mock_config)
        manager3 = SnowflakeConnectionManager(mock_config)

        # get_instance should return same instance
        assert manager1 is manager2
        # Direct constructor should create new instance
        assert manager1 is not manager3

    def test_singleton_thread_safety(self, mock_config):
        """Test that singleton pattern is thread-safe."""
        # Reset singleton
        SnowflakeConnectionManager._instance = None

        instances = []
        threads = []

        def create_instance():
            instance = SnowflakeConnectionManager.get_instance(mock_config)
            instances.append(instance)

        # Create multiple threads that try to get instance
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same
        assert len(set(instances)) == 1
        assert len(instances) == 10

    def test_build_connection_params_password_auth(self, connection_manager):
        """Test building connection parameters for password authentication."""
        params = connection_manager._build_connection_params()

        expected_keys = {"account", "user", "timeout", "password", "role", "warehouse", "database", "schema"}
        assert set(params.keys()) == expected_keys
        assert params["account"] == "test_account"
        assert params["user"] == "test_user"
        assert params["password"] == "test_password"
        assert params["role"] == "test_role"
        assert params["warehouse"] == "test_warehouse"
        assert params["database"] == "test_db"
        assert params["schema"] == "test_schema"

    def test_build_connection_params_private_key_auth(self, mock_config):
        """Test building connection parameters for private key authentication."""
        mock_config.snowflake.auth_type = AuthType.PRIVATE_KEY
        mock_config.snowflake.private_key = "test_private_key"
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        params = manager._build_connection_params()

        assert "private_key" in params
        assert params["private_key"] == "test_private_key"
        assert "password" not in params

    def test_build_connection_params_private_key_file_auth(self, mock_config):
        """Test building connection parameters for private key file authentication."""
        mock_config.snowflake.auth_type = AuthType.PRIVATE_KEY
        mock_config.snowflake.private_key_path = "/path/to/key.pem"
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        params = manager._build_connection_params()

        assert "private_key_file" in params
        assert params["private_key_file"] == "/path/to/key.pem"
        assert "password" not in params

    def test_build_connection_params_external_browser_auth(self, mock_config):
        """Test building connection parameters for external browser authentication."""
        mock_config.snowflake.auth_type = AuthType.EXTERNAL_BROWSER
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        params = manager._build_connection_params()

        assert params["authenticator"] == "externalbrowser"
        assert "password" not in params

    def test_build_connection_params_oauth_auth(self, mock_config):
        """Test building connection parameters for OAuth authentication."""
        mock_config.snowflake.auth_type = AuthType.OAUTH
        mock_config.snowflake.token = "test_oauth_token"
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        params = manager._build_connection_params()

        assert params["authenticator"] == "oauth"
        assert params["token"] == "test_oauth_token"
        assert "password" not in params

    def test_build_connection_params_missing_private_key(self, mock_config):
        """Test error when private key authentication is configured but no key provided."""
        mock_config.snowflake.auth_type = AuthType.PRIVATE_KEY
        mock_config.snowflake.private_key = None
        mock_config.snowflake.private_key_path = None
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        with pytest.raises(ConfigurationError, match="Private key authentication requires"):
            manager._build_connection_params()

    def test_build_connection_params_missing_password(self, mock_config):
        """Test error when password authentication is configured but no password provided."""
        mock_config.snowflake.auth_type = AuthType.PASSWORD
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        with pytest.raises(ConfigurationError, match="Password authentication requires password"):
            manager._build_connection_params()

    def test_build_connection_params_missing_oauth_token(self, mock_config):
        """Test error when OAuth authentication is configured but no token provided."""
        mock_config.snowflake.auth_type = AuthType.OAUTH
        mock_config.snowflake.token = None
        mock_config.snowflake.password = None

        manager = SnowflakeConnectionManager(mock_config)
        with pytest.raises(ConfigurationError, match="OAuth authentication requires token"):
            manager._build_connection_params()

    @patch('snowflake.connector.connect')
    def test_create_connection_success(self, mock_connect, connection_manager):
        """Test successful connection creation."""
        # Mock successful connection
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_cursor.fetchone.return_value = ["9.35.2"]

        # Mock the context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = mock_cursor
        mock_cursor_context.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_connection

        connection = connection_manager._create_connection()

        # Verify connection was created with correct parameters
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[1]
        assert call_args["account"] == "test_account"
        assert call_args["user"] == "test_user"
        assert call_args["password"] == "test_password"

        # Verify connection test query was executed
        mock_cursor.execute.assert_called_once_with("SELECT CURRENT_VERSION()")

        # Verify connection state
        assert connection == mock_connection
        assert connection_manager._connection_healthy is True
        assert connection_manager._last_error is None
        assert connection_manager._last_refresh is not None

    @patch('snowflake.connector.connect')
    def test_create_connection_failure(self, mock_connect, connection_manager):
        """Test connection creation failure."""
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(ConnectionError, match="Failed to connect to Snowflake"):
            connection_manager._create_connection()

        # Verify error state
        assert connection_manager._connection_healthy is False
        assert connection_manager._last_error is not None
        assert "Connection failed" in str(connection_manager._last_error)

    def test_is_connection_stale_no_refresh(self, connection_manager):
        """Test connection staleness when no refresh has occurred."""
        assert connection_manager._is_connection_stale() is True

    def test_is_connection_stale_fresh(self, connection_manager):
        """Test connection staleness for fresh connection."""
        connection_manager._last_refresh = datetime.now(timezone.utc) - timedelta(hours=1)
        assert connection_manager._is_connection_stale() is False

    def test_is_connection_stale_old(self, connection_manager):
        """Test connection staleness for old connection."""
        connection_manager._last_refresh = datetime.now(timezone.utc) - timedelta(hours=10)
        assert connection_manager._is_connection_stale() is True

    @patch('snowflake.connector.connect')
    def test_get_connection_new_connection(self, mock_connect, connection_manager):
        """Test getting a new connection."""
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_cursor.fetchone.return_value = ["9.35.2"]

        # Mock the context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = mock_cursor
        mock_cursor_context.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_connection

        with connection_manager.get_connection(use_dict_cursor=False) as (conn, cursor):
            assert conn == mock_connection
            # Verify cursor was created for the get_connection call (in addition to connection test)
            assert mock_connection.cursor.call_count == 2

        # Verify connection was created
        mock_connect.assert_called_once()

    @patch('snowflake.connector.connect')
    def test_get_connection_dict_cursor(self, mock_connect, connection_manager):
        """Test getting a connection with dict cursor."""
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_cursor = Mock(spec=DictCursor)
        mock_cursor.fetchone.return_value = ["9.35.2"]

        # Mock the context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = mock_cursor
        mock_cursor_context.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_connection

        with connection_manager.get_connection(use_dict_cursor=True) as (conn, cursor):
            assert conn == mock_connection
            # Verify dict cursor was requested (should be the second call)
            assert mock_connection.cursor.call_count == 2
            # Check that the last call was for DictCursor
            mock_connection.cursor.assert_called_with(snowflake.connector.DictCursor)

    @patch('snowflake.connector.connect')
    def test_get_connection_reuse_existing(self, mock_connect, connection_manager):
        """Test reusing existing healthy connection."""
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_cursor.fetchone.return_value = ["9.35.2"]

        # Mock the context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = mock_cursor
        mock_cursor_context.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_connection

        # First call creates connection
        with connection_manager.get_connection() as (conn1, cursor1):
            assert conn1 == mock_connection

        # Reset mock to track second call
        mock_connect.reset_mock()
        mock_connection.cursor.reset_mock()

        # Second call reuses connection
        connection_manager._last_refresh = datetime.now(timezone.utc)  # Fresh connection
        with connection_manager.get_connection() as (conn2, cursor2):
            assert conn2 == mock_connection

        # Connection should not be recreated
        mock_connect.assert_not_called()

    @patch('snowflake.connector.connect')
    def test_get_connection_force_refresh_stale(self, mock_connect, connection_manager):
        """Test connection refresh for stale connection."""
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_cursor.fetchone.return_value = ["9.35.2"]

        # Mock the context manager for cursor
        mock_cursor_context = MagicMock()
        mock_cursor_context.__enter__.return_value = mock_cursor
        mock_cursor_context.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_connection

        # Set up stale connection
        old_connection = Mock(spec=SnowflakeConnection)
        connection_manager._connection = old_connection
        connection_manager._last_refresh = datetime.now(timezone.utc) - timedelta(hours=10)
        connection_manager._connection_healthy = True

        with connection_manager.get_connection() as (conn, cursor):
            assert conn == mock_connection

        # Verify old connection was closed
        old_connection.close.assert_called_once()
        # Verify new connection was created
        mock_connect.assert_called_once()

    def test_is_connection_healthy_no_error(self, connection_manager):
        """Test health check with no errors."""
        connection_manager._connection_healthy = True
        connection_manager._last_error = None
        connection_manager._connection = Mock()
        connection_manager._last_refresh = datetime.now(timezone.utc)  # Fresh connection

        is_healthy, error_msg = connection_manager.is_connection_healthy()
        assert is_healthy is True
        assert error_msg is None

    def test_is_connection_healthy_with_error(self, connection_manager):
        """Test health check with previous error."""
        connection_manager._connection_healthy = False
        connection_manager._last_error = Exception("Test error")

        is_healthy, error_msg = connection_manager.is_connection_healthy()
        assert is_healthy is False
        assert "Test error" in error_msg
        assert "Exception" in error_msg

    def test_is_connection_healthy_no_connection(self, connection_manager):
        """Test health check with no connection."""
        connection_manager._connection = None

        is_healthy, error_msg = connection_manager.is_connection_healthy()
        assert is_healthy is False
        assert error_msg == "No connection established"

    def test_is_connection_healthy_stale(self, connection_manager):
        """Test health check with stale connection."""
        connection_manager._connection = Mock()
        connection_manager._connection_healthy = True
        connection_manager._last_refresh = datetime.now(timezone.utc) - timedelta(hours=10)

        is_healthy, error_msg = connection_manager.is_connection_healthy()
        assert is_healthy is False
        assert "stale" in error_msg

    def test_close_connection(self, connection_manager):
        """Test closing connection."""
        mock_connection = Mock(spec=SnowflakeConnection)
        connection_manager._connection = mock_connection
        connection_manager._connection_healthy = True

        connection_manager.close_connection()

        mock_connection.close.assert_called_once()
        assert connection_manager._connection is None
        assert connection_manager._connection_healthy is False

    def test_close_connection_no_connection(self, connection_manager):
        """Test closing when no connection exists."""
        connection_manager._connection = None

        # Should not raise any error
        connection_manager.close_connection()
        assert connection_manager._connection is None

    def test_close_connection_with_error(self, connection_manager):
        """Test closing connection when close raises error."""
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_connection.close.side_effect = Exception("Close error")
        connection_manager._connection = mock_connection

        # Should not raise error
        connection_manager.close_connection()
        assert connection_manager._connection is None
        assert connection_manager._connection_healthy is False

    def test_refresh_connection(self, connection_manager):
        """Test forcing connection refresh."""
        mock_connection = Mock(spec=SnowflakeConnection)
        connection_manager._connection = mock_connection
        connection_manager._connection_healthy = True

        connection_manager.refresh_connection()

        mock_connection.close.assert_called_once()
        assert connection_manager._connection is None
        assert connection_manager._connection_healthy is False

    def test_get_connection_info(self, connection_manager):
        """Test getting connection information."""
        connection_manager._connection_healthy = True
        connection_manager._last_refresh = datetime.now(timezone.utc)
        connection_manager._last_error = None
        mock_connection = Mock(spec=SnowflakeConnection)
        mock_connection.session_id = "test_session_id"
        connection_manager._connection = mock_connection

        info = connection_manager.get_connection_info()

        expected_keys = {
            "healthy", "last_refresh", "refresh_interval_hours",
            "connection_timeout", "error_message", "session_id"
        }
        assert set(info.keys()) == expected_keys
        assert info["healthy"] is True
        assert info["session_id"] == "test_session_id"
        assert info["refresh_interval_hours"] == 8.0  # Default value
        assert info["connection_timeout"] == 60  # Default value

    def test_get_connection_info_with_error(self, connection_manager):
        """Test getting connection info when there's an error."""
        connection_manager._connection_healthy = False
        connection_manager._last_error = Exception("Test error")

        info = connection_manager.get_connection_info()

        assert info["healthy"] is False
        assert "Test error" in info["error_message"]
        assert "session_id" not in info  # No connection when there's an error


class TestSafeConnectionWrapper:
    """Test cases for SafeConnectionWrapper."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Icebreaker configuration."""
        config = Mock(spec=IcebreakerConfig)
        config.safe_mode = True
        return config

    @pytest.fixture
    def mock_connection_manager(self):
        """Create a mock connection manager."""
        return Mock(spec=SnowflakeConnectionManager)

    @pytest.fixture
    def safe_wrapper(self, mock_connection_manager, mock_config):
        """Create a safe connection wrapper for testing."""
        return SafeConnectionWrapper(mock_connection_manager, mock_config)

    def test_init(self, safe_wrapper, mock_connection_manager, mock_config):
        """Test safe connection wrapper initialization."""
        assert safe_wrapper.connection_manager == mock_connection_manager
        assert safe_wrapper.config == mock_config

    @patch('icebreaker.core.connection.logger')
    def test_execute_safe_query_success(self, mock_logger, safe_wrapper, mock_connection_manager):
        """Test successful safe query execution."""
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_connection = Mock(spec=SnowflakeConnection)

        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = (mock_connection, mock_cursor)
        mock_context.__exit__.return_value = None
        mock_connection_manager.get_connection.return_value = mock_context

        with safe_wrapper.execute_safe_query("SELECT 1") as cursor:
            assert cursor == mock_cursor

        # Verify connection manager was called correctly
        mock_connection_manager.get_connection.assert_called_once_with(use_dict_cursor=False)
        mock_logger.info.assert_called_once()

    @patch('icebreaker.core.connection.logger')
    def test_execute_safe_query_with_dict_cursor(self, mock_logger, safe_wrapper, mock_connection_manager):
        """Test safe query execution with dict cursor."""
        mock_cursor = Mock(spec=DictCursor)
        mock_connection = Mock(spec=SnowflakeConnection)

        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = (mock_connection, mock_cursor)
        mock_context.__exit__.return_value = None
        mock_connection_manager.get_connection.return_value = mock_context

        with safe_wrapper.execute_safe_query("SELECT 1", use_dict_cursor=True) as cursor:
            assert cursor == mock_cursor

        mock_connection_manager.get_connection.assert_called_once_with(use_dict_cursor=True)

    @patch('icebreaker.core.connection.logger')
    def test_execute_safe_query_connection_error(self, mock_logger, safe_wrapper, mock_connection_manager):
        """Test safe query execution when connection fails."""
        mock_connection_manager.get_connection.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            with safe_wrapper.execute_safe_query("SELECT 1"):
                pass

        # Verify error was logged
        mock_logger.error.assert_called_once()

    @patch('icebreaker.core.connection.logger')
    def test_execute_safe_query_logging(self, mock_logger, safe_wrapper, mock_connection_manager):
        """Test that safe query execution logs appropriately."""
        mock_cursor = Mock(spec=SnowflakeCursor)
        mock_connection = Mock(spec=SnowflakeConnection)

        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = (mock_connection, mock_cursor)
        mock_context.__exit__.return_value = None
        mock_connection_manager.get_connection.return_value = mock_context

        sql = "SELECT * FROM test_table"
        with safe_wrapper.execute_safe_query(sql) as cursor:
            pass

        # Verify logging
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[1]
        assert call_args["sql_preview"] == sql[:100]