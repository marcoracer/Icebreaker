"""Pytest configuration and fixtures.

Following diasv_mcp's lightweight testing approach with explicit marker strategy.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import Mock
from pathlib import Path

import pytest

# Add src directory to Python path
TESTS_DIR = Path(__file__).parent
SRC_DIR = TESTS_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def mock_snowflake_config():
    """Mock Snowflake configuration for testing."""
    from icebreaker.core.config import SnowflakeConfig, AuthType

    return SnowflakeConfig(
        account="test_account",
        user="test_user",
        role="test_role",
        warehouse="test_warehouse",
        database="test_database",
        schema_name="test_schema",
        auth_type=AuthType.PASSWORD,
        password="test_password"
    )


@pytest.fixture
def mock_icebreaker_config(mock_snowflake_config):
    """Mock Icebreaker configuration for testing."""
    from icebreaker.core.config import IcebreakerConfig

    return IcebreakerConfig(
        snowflake=mock_snowflake_config,
        safe_mode=True,
        query_timeout=300,
        max_query_results=1000,
        audit_logging=True,
        debug=False,
        environment="testing"
    )


@pytest.fixture
def mock_snowflake_connection():
    """Mock Snowflake connection for unit tests."""
    connection = Mock()

    # Mock cursor context manager
    cursor = Mock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None

    # Mock query execution
    cursor.execute.return_value = None
    cursor.fetchone.return_value = ("test_version", "1.0.0")
    cursor.fetchall.return_value = [
        {"name": "test_db", "created_on": "2024-01-01"},
        {"name": "test_db2", "created_on": "2024-01-02"}
    ]

    connection.cursor.return_value = cursor
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = None

    return connection


@pytest.fixture
def sample_database_metadata():
    """Sample database metadata for testing."""
    return [
        {"name": "PROD_DB", "created_on": "2024-01-01", "owner": "ADMIN"},
        {"name": "DEV_DB", "created_on": "2024-01-02", "owner": "DEV_TEAM"},
        {"name": "TEST_DB", "created_on": "2024-01-03", "owner": "QA"}
    ]


@pytest.fixture
def sample_warehouse_data():
    """Sample warehouse data for testing."""
    return [
        {"name": "COMPUTE_WH", "state": "SUSPENDED", "size": "X-SMALL"},
        {"name": "ANALYTICS_WH", "state": "RUNNING", "size": "MEDIUM"},
        {"name": "LOADING_WH", "state": "SUSPENDED", "size": "LARGE"}
    ]


# Integration test fixtures - require live Snowflake connection
@pytest.fixture
def live_snowflake_config():
    """Live Snowflake configuration for integration tests.

    This fixture requires environment variables to be set:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH
    """
    if not os.getenv("SNOWFLAKE_ACCOUNT"):
        pytest.skip("Snowflake integration tests require SNOWFLAKE_ACCOUNT environment variable")

    try:
        from icebreaker.core.config import IcebreakerConfig
        return IcebreakerConfig.from_environment()
    except Exception as e:
        pytest.skip(f"Cannot create Snowflake configuration: {e}")


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "timeout": 30,
        "retry_attempts": 3,
        "test_database": "ICEBREAKER_TEST_DB",
        "test_warehouse": "ICEBREAKER_TEST_WH"
    }