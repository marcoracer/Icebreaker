"""Icebreaker configuration management.

Combining official Snowflake MCP YAML support with community TOML inspiration
and Pydantic validation patterns from multiple reference implementations.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any, Set

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .logging import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)


class AuthType(str, Enum):
    """Snowflake authentication types."""
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    EXTERNAL_BROWSER = "externalbrowser"
    OAUTH = "oauth"


class ServiceConfig(BaseModel):
    """Service configuration for dynamic tool registration."""

    model_config = ConfigDict(extra="allow")  # Allow additional properties for future extensions

    enabled: bool = Field(True, description="Whether this service tier is enabled")
    tools: List[str] = Field(default_factory=list, description="List of tools available in this service")
    safety_checks: str = Field("normal", description="Safety check level: normal, strict, permissive")


class SQLPermissions(BaseModel):
    """SQL statement permissions configuration."""

    allowed: List[str] = Field(
        default_factory=lambda: ["SELECT", "SHOW", "DESCRIBE", "GET_DDL", "USE", "WITH"],
        description="Allowed SQL statement types"
    )
    administrative_allowed: List[str] = Field(
        default_factory=lambda: [
            "ALTER WAREHOUSE", "CREATE USER", "ALTER USER", "GRANT ROLE",
            "SYSTEM$ABORT_QUERY"
        ],
        description="Administrative SQL statement types"
    )
    disallowed: List[str] = Field(
        default_factory=lambda: [
            "DROP DATABASE", "DROP SCHEMA", "DROP WAREHOUSE", "UNSUPPORTED"
        ],
        description="Always disallowed SQL statement types"
    )


class ToolPermission(BaseModel):
    """Individual tool permission configuration."""

    required_roles: List[str] = Field(default_factory=list, description="Roles required to use this tool")
    safety_checks: bool = Field(True, description="Whether safety checks are required")
    requires_confirmation: bool = Field(False, description="Whether user confirmation is required")
    requires_approval: bool = Field(False, description="Whether approval workflow is required")
    blocked_in_safe_mode: bool = Field(False, description="Whether tool is blocked when safe mode is enabled")


class RoleConfig(BaseModel):
    """Role-based access control configuration."""

    allowed_tools: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of tools this role can access ('*' for all tools)"
    )
    allowed_operations: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of operations this role can perform ('*' for all operations)"
    )


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

    # Service configurations
    discovery: ServiceConfig = Field(default_factory=ServiceConfig, description="Discovery services configuration")
    operational: ServiceConfig = Field(default_factory=ServiceConfig, description="Operational services configuration")
    engineering: ServiceConfig = Field(default_factory=ServiceConfig, description="Engineering services configuration")
    intelligence: ServiceConfig = Field(default_factory=ServiceConfig, description="Intelligence services configuration")

    # SQL permissions
    sql_permissions: SQLPermissions = Field(default_factory=SQLPermissions, description="SQL statement permissions")

    # Role-based access control
    roles: Dict[str, RoleConfig] = Field(
        default_factory=lambda: {
            "analyst": RoleConfig(
                allowed_tools=["list_databases", "list_schemas", "list_tables", "describe_table", "get_object_ddl", "search_objects"],
                allowed_operations=["READ"]
            ),
            "dataops": RoleConfig(
                allowed_tools=["*"],
                allowed_operations=["READ", "WAREHOUSE_MANAGE", "USER_MANAGE_BASIC"]
            ),
            "admin": RoleConfig(
                allowed_tools=["*"],
                allowed_operations=["*"]
            )
        },
        description="Role-based access control configuration"
    )

    # Tool-specific permissions
    tool_permissions: Dict[str, ToolPermission] = Field(
        default_factory=dict,
        description="Tool-specific permission configurations"
    )

    @classmethod
    def from_environment(cls, services_config_path: str = "config/services.yaml",
                        permissions_config_path: str = "config/permissions.yaml") -> IcebreakerConfig:
        """Load configuration from environment variables and config files."""
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

        # Create base configuration
        config = cls(
            snowflake=snowflake_config,
            safe_mode=os.getenv("ICEBREAKER_SAFE_MODE", "true").lower() == "true",
            query_timeout=int(os.getenv("ICEBREAKER_QUERY_TIMEOUT", "300")),
            max_query_results=int(os.getenv("ICEBREAKER_MAX_QUERY_RESULTS", "10000")),
            audit_logging=os.getenv("ICEBREAKER_AUDIT_LOGGING", "true").lower() == "true",
            debug=os.getenv("ICEBREAKER_DEBUG", "false").lower() == "true",
            environment=os.getenv("ICEBREAKER_ENVIRONMENT", "development"),
        )

        # Load and merge services configuration
        try:
            services_config = config.load_services_config(services_config_path)
            if services_config:
                # Update service configurations from file
                if 'discovery' in services_config:
                    config.discovery = ServiceConfig(**services_config['discovery'])
                if 'operational' in services_config:
                    config.operational = ServiceConfig(**services_config['operational'])
                if 'engineering' in services_config:
                    config.engineering = ServiceConfig(**services_config['engineering'])
                if 'intelligence' in services_config:
                    config.intelligence = ServiceConfig(**services_config['intelligence'])

                # Update SQL permissions if provided
                if 'sql_statement_permissions' in services_config:
                    sql_config = services_config['sql_statement_permissions']
                    config.sql_permissions = SQLPermissions(**sql_config)

                logger.info("Services configuration merged from file", file=services_config_path)
        except Exception as e:
            logger.warning("Failed to load services configuration", file=services_config_path, error=str(e))

        # Load and merge permissions configuration
        try:
            permissions_config = config.load_permissions_config(permissions_config_path)
            if permissions_config:
                # Update role configurations from file
                if 'roles' in permissions_config:
                    for role_name, role_config in permissions_config['roles'].items():
                        config.roles[role_name] = RoleConfig(**role_config)

                # Update tool permissions if provided
                if 'tool_permissions' in permissions_config:
                    for tool_name, tool_config in permissions_config['tool_permissions'].items():
                        config.tool_permissions[tool_name] = ToolPermission(**tool_config)

                logger.info("Permissions configuration merged from file", file=permissions_config_path)
        except Exception as e:
            logger.warning("Failed to load permissions configuration", file=permissions_config_path, error=str(e))

        return config

    @classmethod
    def from_file(cls, config_path: str) -> IcebreakerConfig:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def load_services_config(cls, services_config_path: str) -> Dict[str, Any]:
        """Load services configuration from YAML file."""
        config_file = Path(services_config_path)
        if not config_file.exists():
            logger.warning(f"Services config file not found: {config_file_path}, using defaults")
            return {}

        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    @classmethod
    def load_permissions_config(cls, permissions_config_path: str) -> Dict[str, Any]:
        """Load permissions configuration from YAML file."""
        config_file = Path(permissions_config_path)
        if not config_file.exists():
            logger.warning(f"Permissions config file not found: {permissions_config_path}, using defaults")
            return {}

        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    def get_enabled_services(self) -> Dict[str, ServiceConfig]:
        """Get all enabled service configurations."""
        return {
            'discovery': self.discovery,
            'operational': self.operational,
            'engineering': self.engineering,
            'intelligence': self.intelligence
        }

    def get_enabled_tools(self) -> List[str]:
        """Get all enabled tools across all services."""
        tools = []
        for service in self.get_enabled_services().values():
            if service.enabled:
                if service.tools == ["*"]:
                    # TODO: Auto-discover tools from modules when implemented
                    tools.extend([])  # Placeholder for auto-discovery
                else:
                    tools.extend(service.tools)
        return list(set(tools))  # Remove duplicates

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a specific tool is enabled."""
        for service in self.get_enabled_services().values():
            if service.enabled:
                if service.tools == ["*"]:
                    return True  # All tools enabled for this service
                elif tool_name in service.tools:
                    return True
        return False

    def check_permission(self, tool_name: str, user_role: str) -> bool:
        """Check if a user role has permission to use a tool."""
        # Check role-based permissions
        if user_role in self.roles:
            role_config = self.roles[user_role]
            if "*" in role_config.allowed_tools or tool_name in role_config.allowed_tools:
                return True

        # Check tool-specific permissions
        if tool_name in self.tool_permissions:
            tool_permission = self.tool_permissions[tool_name]
            if not tool_permission.required_roles:
                return True  # No role restrictions
            if user_role in tool_permission.required_roles:
                return True

        return False

    def is_safe_for_operation(self, tool_name: str, operation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if an operation is safe based on tool permissions and safe mode."""
        if not self.safe_mode:
            return {"allowed": True, "reason": "Safe mode is disabled"}

        tool_permission = self.tool_permissions.get(tool_name, ToolPermission())

        # Check if tool is blocked in safe mode
        if tool_permission.blocked_in_safe_mode:
            return {
                "allowed": False,
                "reason": f"Tool '{tool_name}' is blocked in safe mode"
            }

        # Check if confirmation is required
        if tool_permission.requires_confirmation:
            return {
                "allowed": False,
                "requires_confirmation": True,
                "reason": f"Tool '{tool_name}' requires user confirmation"
            }

        # Check if approval is required
        if tool_permission.requires_approval:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": f"Tool '{tool_name}' requires approval workflow"
            }

        return {"allowed": True, "reason": "Operation is allowed"}