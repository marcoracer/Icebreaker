"""Unit tests for error classes."""

import pytest

from icebreaker.core.errors import (
    IcebreakerError,
    ValidationError,
    NotFoundError,
    ConflictError,
    SafeModeError,
    SnowflakeConnectionError,
    PermissionDeniedError,
    ConfigurationError
)


class TestIcebreakerErrors:
    """Test Icebreaker error hierarchy and behavior."""

    @pytest.mark.unit
    def test_base_error_creation(self):
        """Test base IcebreakerError creation."""
        error = IcebreakerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_validation_error(self):
        """Test ValidationError creation and inheritance."""
        error = ValidationError("Invalid input provided")
        assert str(error) == "Invalid input provided"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, ValidationError)

    @pytest.mark.unit
    def test_not_found_error(self):
        """Test NotFoundError creation and inheritance."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, NotFoundError)

    @pytest.mark.unit
    def test_conflict_error(self):
        """Test ConflictError creation and inheritance."""
        error = ConflictError("Resource conflict detected")
        assert str(error) == "Resource conflict detected"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, ConflictError)

    @pytest.mark.unit
    def test_safe_mode_error(self):
        """Test SafeModeError creation and inheritance."""
        error = SafeModeError("Operation blocked by safe mode")
        assert str(error) == "Operation blocked by safe mode"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, SafeModeError)

    @pytest.mark.unit
    def test_snowflake_connection_error(self):
        """Test SnowflakeConnectionError creation and inheritance."""
        error = SnowflakeConnectionError("Failed to connect to Snowflake")
        assert str(error) == "Failed to connect to Snowflake"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, SnowflakeConnectionError)

    @pytest.mark.unit
    def test_permission_denied_error(self):
        """Test PermissionDeniedError creation and inheritance."""
        error = PermissionDeniedError("Insufficient permissions")
        assert str(error) == "Insufficient permissions"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, PermissionDeniedError)

    @pytest.mark.unit
    def test_configuration_error(self):
        """Test ConfigurationError creation and inheritance."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, IcebreakerError)
        assert isinstance(error, ConfigurationError)

    @pytest.mark.unit
    def test_error_catch_hierarchy(self):
        """Test that all errors can be caught as IcebreakerError."""
        errors = [
            ValidationError("test"),
            NotFoundError("test"),
            ConflictError("test"),
            SafeModeError("test"),
            SnowflakeConnectionError("test"),
            PermissionDeniedError("test"),
            ConfigurationError("test"),
        ]

        for error in errors:
            try:
                raise error
            except IcebreakerError as e:
                assert str(e) == "test"
            except Exception:
                pytest.fail(f"Error {type(error)} should be caught as IcebreakerError")

    @pytest.mark.unit
    def test_error_with_none_message(self):
        """Test error creation with None message."""
        error = ValidationError(None)
        # str() should handle None gracefully
        assert "None" in str(error) or str(error) == ""

    @pytest.mark.unit
    def test_error_with_empty_message(self):
        """Test error creation with empty message."""
        error = ValidationError("")
        assert str(error) == ""

    @pytest.mark.unit
    def test_error_with_long_message(self):
        """Test error creation with long message."""
        long_message = "A" * 1000
        error = ValidationError(long_message)
        assert str(error) == long_message

    @pytest.mark.unit
    def test_error_chaining(self):
        """Test error chaining (exception chaining)."""
        try:
            raise ValueError("Original error")
        except ValueError as original_error:
            try:
                raise ValidationError("Wrapped error") from original_error
            except ValidationError as chained_error:
                # Check that the exception chain is preserved
                assert chained_error.__cause__ is original_error
                assert isinstance(original_error, ValueError)
                assert str(original_error) == "Original error"
                assert str(chained_error) == "Wrapped error"
                return  # Test passed

        pytest.fail("Error chaining test failed")