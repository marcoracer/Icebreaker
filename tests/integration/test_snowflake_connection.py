"""Integration tests for Snowflake connection.

These tests require a live Snowflake connection and valid credentials.
Run with: pytest -m integration

🚨 IMPORTANT: Integration tests will only run when you provide Snowflake credentials in .env
"""

import pytest

from icebreaker.core.config import IcebreakerConfig


@pytest.mark.integration
class TestSnowflakeConnection:
    """Integration tests for live Snowflake connection."""

    @pytest.mark.integration
    def test_environment_configuration_validation(self, live_snowflake_config):
        """Test that environment configuration is valid."""
        assert live_snowflake_config.snowflake.account is not None
        assert live_snowflake_config.snowflake.user is not None
        assert len(live_snowflake_config.snowflake.account) > 0
        assert len(live_snowflake_config.snowflake.user) > 0

    @pytest.mark.integration
    def test_basic_snowflake_connection(self, live_snowflake_config, integration_test_config):
        """Test basic Snowflake connection establishment."""
        # This test will be implemented when we add connection logic
        # For now, it validates that we can load configuration
        pytest.skip("Connection logic not yet implemented - will be added in Phase 1")

    @pytest.mark.integration
    def test_simple_query_execution(self, live_snowflake_config, integration_test_config):
        """Test simple query execution against live Snowflake."""
        # This test will be implemented when we add query execution logic
        pytest.skip("Query execution logic not yet implemented - will be added in Phase 1")

    @pytest.mark.integration
    def test_database_listing(self, live_snowflake_config, integration_test_config):
        """Test database listing against live Snowflake."""
        # This test will be implemented when we add discovery tools
        pytest.skip("Discovery tools not yet implemented - will be added in Phase 1")


@pytest.mark.integration
class TestSnowflakeConfiguration:
    """Integration tests for Snowflake configuration with live credentials."""

    @pytest.mark.integration
    def test_private_key_authentication(self):
        """Test configuration with private key authentication."""
        # This test will run if SNOWFLAKE_PRIVATE_KEY_PATH or SNOWFLAKE_PRIVATE_KEY is set
        pytest.skip("Private key authentication testing not yet implemented")

    @pytest.mark.integration
    def test_password_authentication(self):
        """Test configuration with password authentication."""
        # This test will run if SNOWFLAKE_PASSWORD is set
        pytest.skip("Password authentication testing not yet implemented")

    @pytest.mark.integration
    def test_external_browser_authentication(self):
        """Test configuration with external browser authentication."""
        # This test will run if SNOWFLAKE_AUTHENTICATOR=externalbrowser is set
        pytest.skip("External browser authentication testing not yet implemented")


# Integration test setup helper
@pytest.mark.integration
def test_integration_setup_instructions():
    """Provide clear instructions for running integration tests.

    This test serves as documentation for developers.
    """
    instructions = """
    🚨 INTEGRATION TEST SETUP INSTRUCTIONS 🚨

    To run integration tests, you need to:

    1. Copy .env.example to .env
    2. Fill in your Snowflake credentials in .env:

       # Required:
       SNOWFLAKE_ACCOUNT=your_account_identifier
       SNOWFLAKE_USER=your_username

       # Choose ONE authentication method:
       SNOWFLAKE_PASSWORD=your_password
       OR
       SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
       OR
       SNOWFLAKE_AUTHENTICATOR=externalbrowser

    3. Run integration tests:
       pytest -m integration

    4. Run specific integration test:
       pytest tests/integration/test_snowflake_connection.py::TestSnowflakeConnection::test_basic_snowflake_connection -v -s

    📋 CURRENT STATUS: Integration tests are placeholders until Phase 1 implementation
    """

    # This test always "passes" but provides documentation
    assert True, instructions