"""Unit tests for configuration management."""

import os
import pytest
from unittest.mock import patch

from icebreaker.core.config import IcebreakerConfig, SnowflakeConfig, AuthType
from icebreaker.core.errors import ConfigurationError


class TestSnowflakeConfig:
    """Test Snowflake configuration validation."""

    @pytest.mark.unit
    def test_valid_private_key_config(self):
        """Test valid configuration with private key auth."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            auth_type=AuthType.PRIVATE_KEY,
            private_key="-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----"
        )

        assert config.account == "test_account"
        assert config.user == "test_user"
        assert config.auth_type == AuthType.PRIVATE_KEY

    @pytest.mark.unit
    def test_valid_password_config(self):
        """Test valid configuration with password auth."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            auth_type=AuthType.PASSWORD,
            password="test_password"
        )

        assert config.auth_type == AuthType.PASSWORD
        assert config.password == "test_password"

    @pytest.mark.unit
    def test_empty_account_raises_error(self):
        """Test that empty account raises validation error."""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            SnowflakeConfig(
                account="",
                user="test_user",
                auth_type=AuthType.PASSWORD
            )

    @pytest.mark.unit
    def test_whitespace_only_account_raises_error(self):
        """Test that whitespace-only account raises validation error."""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            SnowflakeConfig(
                account="   ",
                user="test_user",
                auth_type=AuthType.PASSWORD
            )

    @pytest.mark.unit
    def test_nonexistent_private_key_path_raises_error(self):
        """Test that nonexistent private key path raises error."""
        with pytest.raises(ValueError, match="Private key file not found"):
            SnowflakeConfig(
                account="test_account",
                user="test_user",
                auth_type=AuthType.PRIVATE_KEY,
                private_key_path="/nonexistent/key.pem"
            )

    @pytest.mark.unit
    def test_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            auth_type=AuthType.PASSWORD,
            password="test_password",
            role=None,
            warehouse=None,
            database=None,
            schema_name=None
        )

        assert config.role is None
        assert config.warehouse is None
        assert config.database is None
        assert config.schema_name is None


class TestIcebreakerConfig:
    """Test Icebreaker configuration."""

    @pytest.mark.unit
    def test_default_config_values(self, mock_snowflake_config):
        """Test default configuration values."""
        config = IcebreakerConfig(snowflake=mock_snowflake_config)

        assert config.safe_mode is True
        assert config.query_timeout == 300
        assert config.max_query_results == 10000
        assert config.audit_logging is True
        assert config.debug is False
        assert config.environment == "development"

    @pytest.mark.unit
    def test_custom_config_values(self, mock_snowflake_config):
        """Test custom configuration values."""
        config = IcebreakerConfig(
            snowflake=mock_snowflake_config,
            safe_mode=False,
            query_timeout=600,
            max_query_results=50000,
            audit_logging=False,
            debug=True,
            environment="production"
        )

        assert config.safe_mode is False
        assert config.query_timeout == 600
        assert config.max_query_results == 50000
        assert config.audit_logging is False
        assert config.debug is True
        assert config.environment == "production"

    @pytest.mark.unit
    def test_query_timeout_validation(self, mock_snowflake_config):
        """Test query timeout validation."""
        # Valid range
        IcebreakerConfig(snowflake=mock_snowflake_config, query_timeout=1)
        IcebreakerConfig(snowflake=mock_snowflake_config, query_timeout=3600)

        # Invalid range
        with pytest.raises(ValueError):
            IcebreakerConfig(snowflake=mock_snowflake_config, query_timeout=0)

        with pytest.raises(ValueError):
            IcebreakerConfig(snowflake=mock_snowflake_config, query_timeout=3601)

    @pytest.mark.unit
    def test_max_query_results_validation(self, mock_snowflake_config):
        """Test max query results validation."""
        # Valid range
        IcebreakerConfig(snowflake=mock_snowflake_config, max_query_results=1)
        IcebreakerConfig(snowflake=mock_snowflake_config, max_query_results=100000)

        # Invalid range
        with pytest.raises(ValueError):
            IcebreakerConfig(snowflake=mock_snowflake_config, max_query_results=0)

        with pytest.raises(ValueError):
            IcebreakerConfig(snowflake=mock_snowflake_config, max_query_results=100001)


class TestConfigFromEnvironment:
    """Test loading configuration from environment variables."""

    @pytest.mark.unit
    @patch.dict(os.environ, {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_password"
    })
    def test_from_environment_with_password(self):
        """Test loading config with password authentication."""
        config = IcebreakerConfig.from_environment()

        assert config.snowflake.account == "test_account"
        assert config.snowflake.user == "test_user"
        assert config.snowflake.auth_type == AuthType.PASSWORD
        assert config.snowflake.password == "test_password"

    @pytest.mark.unit
    @patch.dict(os.environ, {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"
    })
    def test_from_environment_with_private_key(self):
        """Test loading config with private key authentication."""
        config = IcebreakerConfig.from_environment()

        assert config.snowflake.account == "test_account"
        assert config.snowflake.user == "test_user"
        assert config.snowflake.auth_type == AuthType.PRIVATE_KEY
        assert config.snowflake.private_key is not None

    @pytest.mark.unit
    @patch.dict(os.environ, {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_AUTHENTICATOR": "externalbrowser"
    })
    def test_from_environment_with_external_browser(self):
        """Test loading config with external browser authentication."""
        config = IcebreakerConfig.from_environment()

        assert config.snowflake.account == "test_account"
        assert config.snowflake.user == "test_user"
        assert config.snowflake.auth_type == AuthType.EXTERNAL_BROWSER

    @pytest.mark.unit
    @patch.dict(os.environ, {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_password",
        "ICEBREAKER_SAFE_MODE": "false",
        "ICEBREAKER_QUERY_TIMEOUT": "600",
        "ICEBREAKER_MAX_QUERY_RESULTS": "50000",
        "ICEBREAKER_DEBUG": "true",
        "ICEBREAKER_ENVIRONMENT": "production"
    })
    def test_from_environment_with_icebreaker_settings(self):
        """Test loading config with Icebreaker-specific settings."""
        config = IcebreakerConfig.from_environment()

        assert config.safe_mode is False
        assert config.query_timeout == 600
        assert config.max_query_results == 50000
        assert config.debug is True
        assert config.environment == "production"

    @pytest.mark.unit
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_missing_required_fields(self):
        """Test that missing required fields raise appropriate errors."""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            IcebreakerConfig.from_environment()