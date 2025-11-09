"""Icebreaker configuration management.

Combining official Snowflake MCP YAML support with community TOML inspiration
and Pydantic validation patterns from multiple reference implementations.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
load_dotenv()


class AuthType(str, Enum):
    """Snowflake authentication types."""
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    EXTERNAL_BROWSER = "externalbrowser"
    OAUTH = "oauth"


class SnowflakeConfig(BaseModel):
    """Snowflake connection configuration."""

    account: str = Field(..., description="Snowflake account identifier")
    user: str = Field(..., description="Snowflake username")
    role: Optional[str] = Field(None, description="Default role")
    warehouse: Optional[str] = Field(None, description="Default warehouse")
    database: Optional[str] = Field(None, description="Default database")
    schema_name: Optional[str] = Field(None, description="Default schema")
    auth_type: AuthType = Field(AuthType.PRIVATE_KEY, description="Authentication method")
    private_key_path: Optional[str] = Field(None, description="Path to private key file")
    private_key: Optional[str] = Field(None, description="Embedded private key")
    password: Optional[str] = Field(None, description="Password for password auth")
    authenticator: Optional[str] = Field(None, description="Authenticator type")
    token: Optional[str] = Field(None, description="OAuth token")

    @field_validator("account", "user")
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        """Validate required string fields."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("private_key_path")
    @classmethod
    def validate_private_key_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate private key path if provided."""
        if v and not Path(v).exists():
            raise ValueError(f"Private key file not found: {v}")
        return v


class IcebreakerConfig(BaseModel):
    """Main Icebreaker configuration."""

    snowflake: SnowflakeConfig
    safe_mode: bool = Field(True, description="Enable safe mode operations")
    query_timeout: int = Field(300, description="Query timeout in seconds", ge=1, le=3600)
    max_query_results: int = Field(10000, description="Maximum query results", ge=1, le=100000)
    audit_logging: bool = Field(True, description="Enable audit logging")
    debug: bool = Field(False, description="Enable debug mode")
    environment: Literal["development", "staging", "production"] = Field("development")

    @classmethod
    def from_environment(cls) -> IcebreakerConfig:
        """Load configuration from environment variables."""
        # Determine auth type based on available credentials
        auth_type = AuthType.PRIVATE_KEY
        if os.getenv("SNOWFLAKE_PASSWORD"):
            auth_type = AuthType.PASSWORD
        elif os.getenv("SNOWFLAKE_AUTHENTICATOR") == "externalbrowser":
            auth_type = AuthType.EXTERNAL_BROWSER
        elif os.getenv("SNOWFLAKE_TOKEN"):
            auth_type = AuthType.OAUTH

        snowflake_config = SnowflakeConfig(
            account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
            user=os.getenv("SNOWFLAKE_USER", ""),
            role=os.getenv("SNOWFLAKE_ROLE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema_name=os.getenv("SNOWFLAKE_SCHEMA"),
            auth_type=auth_type,
            private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
            private_key=os.getenv("SNOWFLAKE_PRIVATE_KEY"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            authenticator=os.getenv("SNOWFLAKE_AUTHENTICATOR"),
            token=os.getenv("SNOWFLAKE_TOKEN"),
        )

        return cls(
            snowflake=snowflake_config,
            safe_mode=os.getenv("ICEBREAKER_SAFE_MODE", "true").lower() == "true",
            query_timeout=int(os.getenv("ICEBREAKER_QUERY_TIMEOUT", "300")),
            max_query_results=int(os.getenv("ICEBREAKER_MAX_QUERY_RESULTS", "10000")),
            audit_logging=os.getenv("ICEBREAKER_AUDIT_LOGGING", "true").lower() == "true",
            debug=os.getenv("ICEBREAKER_DEBUG", "false").lower() == "true",
            environment=os.getenv("ICEBREAKER_ENVIRONMENT", "development"),
        )

    @classmethod
    def from_file(cls, config_path: str) -> IcebreakerConfig:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)