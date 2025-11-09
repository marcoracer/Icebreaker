"""Permission system for Icebreaker MCP Server.

Role-based access control and safety validation middleware.
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum

from .config import IcebreakerConfig, ToolPermission
from .logging import get_logger

logger = get_logger(__name__)


class OperationType(str, Enum):
    """Types of operations that can be performed."""
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    ADMIN = "ADMIN"
    WAREHOUSE_MANAGE = "WAREHOUSE_MANAGE"
    USER_MANAGE_BASIC = "USER_MANAGE_BASIC"
    USER_MANAGE_ADMIN = "USER_MANAGE_ADMIN"
    SCHEMA_MANAGE = "SCHEMA_MANAGE"
    ALL = "*"


class SafetyLevel(str, Enum):
    """Safety check levels."""
    PERMISSIVE = "permissive"
    NORMAL = "normal"
    STRICT = "strict"


class PermissionResult:
    """Result of a permission check."""

    def __init__(
        self,
        allowed: bool,
        reason: str,
        requires_confirmation: bool = False,
        requires_approval: bool = False,
        safety_level: SafetyLevel = SafetyLevel.NORMAL
    ):
        self.allowed = allowed
        self.reason = reason
        self.requires_confirmation = requires_confirmation
        self.requires_approval = requires_approval
        self.safety_level = safety_level


class PermissionManager:
    """Manages permissions and safety checks for Icebreaker operations."""

    def __init__(self, config: IcebreakerConfig):
        self.config = config
        self._permission_cache: Dict[str, Dict[str, bool]] = {}

    def check_tool_permission(
        self,
        tool_name: str,
        user_role: str,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> PermissionResult:
        """Check if a user role has permission to use a specific tool."""

        # Check cache first
        cache_key = f"{tool_name}:{user_role}"
        if cache_key in self._permission_cache:
            cached_result = self._permission_cache[cache_key]
            if cached_result:
                return PermissionResult(
                    allowed=True,
                    reason=f"Cached permission for role '{user_role}' on tool '{tool_name}'"
                )

        # Check if tool is enabled in configuration
        if not self.config.is_tool_enabled(tool_name):
            logger.warning("Tool not enabled in configuration", tool=tool_name, role=user_role)
            return PermissionResult(
                allowed=False,
                reason=f"Tool '{tool_name}' is not enabled in configuration"
            )

        # Check role-based permissions
        role_allowed = self.config.check_permission(tool_name, user_role)
        if not role_allowed:
            logger.warning("Role does not have permission for tool", tool=tool_name, role=user_role)
            return PermissionResult(
                allowed=False,
                reason=f"Role '{user_role}' does not have permission for tool '{tool_name}'"
            )

        # Check tool-specific permissions and safety
        safety_result = self.config.is_safe_for_operation(tool_name, operation_context)
        if not safety_result["allowed"]:
            logger.info(
                "Operation blocked by safety checks",
                tool=tool_name,
                role=user_role,
                reason=safety_result["reason"]
            )
            return PermissionResult(
                allowed=False,
                reason=safety_result["reason"],
                requires_confirmation=safety_result.get("requires_confirmation", False),
                requires_approval=safety_result.get("requires_approval", False)
            )

        # Cache successful permission check
        self._permission_cache[cache_key] = True

        return PermissionResult(
            allowed=True,
            reason=f"Role '{user_role}' has permission for tool '{tool_name}'"
        )

    def check_sql_permission(
        self,
        sql_statement: str,
        user_role: str,
        operation_context: Optional[Dict[str, Any]] = None
    ) -> PermissionResult:
        """Check if a user role has permission to execute a SQL statement."""

        sql_upper = sql_statement.strip().upper()

        # Check if statement type is allowed
        allowed_patterns = self.config.sql_permissions.allowed
        admin_patterns = self.config.sql_permissions.administrative_allowed
        disallowed_patterns = self.config.sql_permissions.disallowed

        # Check disallowed statements first
        for disallowed in disallowed_patterns:
            if sql_upper.startswith(disallowed.upper()):
                logger.warning(
                    "SQL statement blocked - disallowed operation",
                    statement_type=disallowed,
                    role=user_role
                )
                return PermissionResult(
                    allowed=False,
                    reason=f"SQL operation '{disallowed}' is not allowed"
                )

        # Check administrative statements
        for admin_stmt in admin_patterns:
            if sql_upper.startswith(admin_stmt.upper()):
                # Check if role has administrative permissions
                if self._has_operation_permission(user_role, OperationType.ADMIN):
                    return PermissionResult(
                        allowed=True,
                        reason=f"Role '{user_role}' has administrative permissions"
                    )
                else:
                    logger.warning(
                        "SQL statement blocked - insufficient permissions for admin operation",
                        statement_type=admin_stmt,
                        role=user_role
                    )
                    return PermissionResult(
                        allowed=False,
                        reason=f"Role '{user_role}' lacks administrative permissions for '{admin_stmt}'"
                    )

        # Check regular allowed statements
        for allowed in allowed_patterns:
            if sql_upper.startswith(allowed.upper()):
                return PermissionResult(
                    allowed=True,
                    reason=f"SQL operation '{allowed}' is allowed"
                )

        # If no pattern matches, check if role has broad permissions
        if self._has_operation_permission(user_role, OperationType.ALL):
            return PermissionResult(
                allowed=True,
                reason=f"Role '{user_role}' has broad SQL permissions"
            )

        logger.warning(
            "SQL statement blocked - no matching permission pattern",
            statement_start=sql_upper[:50],
            role=user_role
        )
        return PermissionResult(
            allowed=False,
            reason="SQL statement type not recognized or not permitted"
        )

    def _has_operation_permission(self, user_role: str, operation: OperationType) -> bool:
        """Check if a role has permission for a specific operation type."""
        if user_role not in self.config.roles:
            return False

        role_config = self.config.roles[user_role]

        # Check for wildcard permission
        if "*" in role_config.allowed_operations:
            return True

        # Check for specific operation
        if operation in role_config.allowed_operations:
            return True

        # Check for admin operations (includes many sub-types)
        if operation in [OperationType.ADMIN, OperationType.WAREHOUSE_MANAGE,
                        OperationType.USER_MANAGE_ADMIN, OperationType.SCHEMA_MANAGE]:
            if OperationType.ADMIN in role_config.allowed_operations:
                return True

        return False

    def get_effective_permissions(self, user_role: str) -> Dict[str, Any]:
        """Get the effective permissions for a user role."""
        if user_role not in self.config.roles:
            return {
                "allowed_tools": [],
                "allowed_operations": [],
                "effective_permissions": "none"
            }

        role_config = self.config.roles[user_role]
        enabled_tools = self.config.get_enabled_tools()

        # Filter enabled tools based on role permissions
        effective_tools = []
        for tool in enabled_tools:
            if self.config.check_permission(tool, user_role):
                tool_permission = self.config.tool_permissions.get(tool, ToolPermission())
                effective_tools.append({
                    "name": tool,
                    "requires_confirmation": tool_permission.requires_confirmation,
                    "requires_approval": tool_permission.requires_approval,
                    "blocked_in_safe_mode": tool_permission.blocked_in_safe_mode
                })

        return {
            "allowed_tools": [tool["name"] for tool in effective_tools],
            "allowed_operations": role_config.allowed_operations,
            "effective_permissions": "custom",
            "tool_details": effective_tools,
            "safe_mode_enabled": self.config.safe_mode
        }

    def clear_permission_cache(self) -> None:
        """Clear the permission cache."""
        self._permission_cache.clear()
        logger.info("Permission cache cleared")

    def validate_operation_context(
        self,
        tool_name: str,
        operation_context: Dict[str, Any]
    ) -> PermissionResult:
        """Validate operation context for safety checks."""

        # Check for potentially dangerous operations
        dangerous_patterns = [
            "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "CREATE", "ALTER"
        ]

        # Extract SQL from context if present
        sql_statement = operation_context.get("sql", "")
        if sql_statement:
            sql_upper = sql_statement.upper()

            # Check for dangerous patterns in safe mode
            if self.config.safe_mode:
                for pattern in dangerous_patterns:
                    if pattern in sql_upper:
                        logger.warning(
                            "Potentially dangerous operation detected in safe mode",
                            tool=tool_name,
                            pattern=pattern
                        )
                        return PermissionResult(
                            allowed=False,
                            reason=f"Operation '{pattern}' not allowed in safe mode",
                            requires_confirmation=True
                        )

        # Validate warehouse operations
        if "warehouse" in operation_context:
            warehouse_name = operation_context["warehouse"]
            if not warehouse_name or not isinstance(warehouse_name, str):
                return PermissionResult(
                    allowed=False,
                    reason="Invalid warehouse name in operation context"
                )

        return PermissionResult(
            allowed=True,
            reason="Operation context validation passed"
        )