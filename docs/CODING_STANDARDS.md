# Icebreaker MCP Server - Coding Standards

## Requirements

- **Python**: 3.12+
- **Dependency Management**: `uv` with `pyproject.toml`
- **Testing**: `pytest` only

## Package Naming Convention

**IMPORTANT**: To avoid Python import confusion:

- **Project Name**: `icebreaker-mcp` (with hyphen, for distribution)
- **Package Name**: `icebreaker` (without hyphen, for imports)
- **Import Statement**: `import icebreaker`
- **CLI Command**: `icebreaker-mcp` (with hyphen)

**Example Usage:**
```python
# Python import (no hyphen)
import icebreaker
from icebreaker.core.config import IcebreakerConfig

# Command line (with hyphen)
icebreaker-mcp --help
```

## Project Structure

```
icebreaker-mcp/
├── src/icebreaker/              # Main package (src layout)
│   ├── __init__.py
│   ├── server.py               # FastMCP server entry point
│   ├── core/                   # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── connection.py      # Snowflake connection management
│   │   ├── errors.py          # Custom error classes
│   │   └── logging.py         # Logging setup
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── discovery_service.py      # Tier 1: Data discovery
│   │   ├── query_service.py         # Tier 1: Query execution
│   │   ├── compute_service.py       # Tier 2: Warehouse management
│   │   ├── user_service.py          # Tier 2: User management
│   │   ├── admin_service.py         # Tier 2: Administrative operations
│   │   ├── pipeline_service.py      # Tier 3: Data pipelines
│   │   └── intelligence_service.py  # Tier 4: Advanced analytics
│   ├── tools/                 # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── discovery_tools.py
│   │   ├── operational_tools.py
│   │   ├── engineering_tools.py
│   │   └── intelligence_tools.py
│   ├── models/                # Data models and DTOs
│   │   ├── __init__.py
│   │   ├── base.py           # Base models
│   │   ├── discovery.py      # Discovery-related models
│   │   └── operations.py     # Operations-related models
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── validators.py     # Input validation
│       ├── formatters.py     # Data formatting
│       └── safety.py         # Safety checks and guards
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures
├── docs/                     # Documentation
├── config/                   # Configuration files
│   ├── services.yaml        # Service specifications
│   └── permissions.yaml     # SQL permission matrix
├── pyproject.toml           # Project configuration
└── README.md
```

## Naming Conventions

### Python Naming Standards

- **Files and Directories**: `snake_case` (e.g., `discovery_service.py`)
- **Classes**: `PascalCase` (e.g., `DiscoveryService`, `SnowflakeConnection`)
- **Functions and Variables**: `snake_case` (e.g., `execute_query`, `warehouse_name`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_QUERY_LIMIT`, `MAX_RETRY_ATTEMPTS`)
- **Private Members**: Prefix with underscore (e.g., `_validate_permissions()`)
- **Properties**: Use `@property` decorator for computed attributes

### MCP Tool Naming

- **Tool Names**: `verb_noun` pattern (e.g., `list_databases`, `suspend_warehouse`)
- **Tool Descriptions**: Clear, action-oriented descriptions with safety notes where applicable
- **Parameter Names**: Descriptive `snake_case` (e.g., `database_name`, `timeout_seconds`)

## SOLID Principles

Adhere to SOLID principles for maintainable, testable code:
- **SRP**: Single responsibility for each tool and service
- **OCP**: Open for extension, closed for modification
- **LSP**: Subtypes must be substitutable for base types
- **ISP**: Client-specific interfaces, not general-purpose ones
- **DIP**: Depend on abstractions, not concretions

## Error Handling

### Custom Exception Hierarchy

```python
class IcebreakerError(Exception):
    """Base exception for all Icebreaker errors."""
    pass

class ValidationError(IcebreakerError):
    """Raised when input validation fails."""
    pass

class SnowflakeConnectionError(IcebreakerError):
    """Raised when Snowflake connection fails."""
    pass

class PermissionDeniedError(IcebreakerError):
    """Raised when operation is not permitted."""
    pass

class SafeModeError(IcebreakerError):
    """Raised when safe mode prevents an operation."""
    pass
```

### Error Handling Patterns

1. Validate inputs before processing
2. Use specific exception types
3. Log errors with context and severity
4. Never expose sensitive data in error messages
5. Implement graceful degradation for non-critical operations

## Logging Standards

### Logging Configuration

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Logging Levels and Usage

- **DEBUG**: Detailed information for debugging (disabled in production)
- **INFO**: General information about normal operations
- **WARNING**: Potentially harmful situations that don't prevent execution
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Very severe errors that could cause the application to stop

### Logging Best Practices

Use structured logging with contextual information:
```python
logger = structlog.get_logger(__name__)

def suspend_warehouse(self, name: str, force: bool = False):
    logger.info("warehouse.suspend.requested", warehouse=name, force=force)

    try:
        result = self._perform_suspend(name)
        logger.info("warehouse.suspend.completed", warehouse=name, status=result['status'])
        return result
    except Exception as e:
        logger.error("warehouse.suspend.failed", warehouse=name, error=str(e))
        raise
```

## Testing

Use `pytest` for all testing with mandatory markers:

### Test Categories & Markers

- **Unit Tests**: Fast, isolated tests without external dependencies
  - `@pytest.mark.unit`: Tests that don't require live Snowflake connections
  - Use mocks and fixtures for all external dependencies
  - Should run in < 100ms per test

- **Integration Tests**: Tests requiring live external services
  - `@pytest.mark.integration`: Tests that hit actual Snowflake API
  - Require credentials in `.env` file
  - Can be slower and require network access

- **Contract Tests**: Test MCP tool contracts and interfaces
  - `@pytest.mark.contract`: Verify tool input/output contracts
  - Test error handling and edge cases

- **Safety Tests**: Test safety mechanisms and error conditions
  - `@pytest.mark.safety`: Verify safety validations work correctly
  - Test security controls and governance features

### pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-q -m 'not integration'"
markers = [
    "unit: Fast tests without external dependencies (default)",
    "integration: Tests requiring live Snowflake connection",
    "contract: MCP tool contract verification tests",
    "safety: Safety mechanism and security tests",
]
```

### Running Tests

```bash
# Default: run only unit tests (fast)
pytest

# Run integration tests (requires .env credentials)
pytest -m integration

# Run specific test categories
pytest -m "unit or contract"
pytest -m "safety"

# Run all tests
pytest -m "unit or integration or contract or safety"
```

### Testing Examples

```python
import pytest
from unittest.mock import Mock

class TestWarehouseService:
    @pytest.fixture
    def service(self):
        mock_connection = Mock()
        return WarehouseService(connection=mock_connection)

    @pytest.mark.unit
    def test_suspend_warehouse_success(self, service):
        """Unit test for successful warehouse suspension."""
        service._perform_suspend = Mock(return_value={'status': 'suspended'})

        result = service.suspend_warehouse("TEST_WH")

        assert result['status'] == 'suspended'
        service._perform_suspend.assert_called_once_with("TEST_WH")

    @pytest.mark.unit
    def test_suspend_warehouse_blocked_by_active_queries(self, service):
        """Unit test for safety validation."""
        service._has_active_queries = Mock(return_value=True)

        with pytest.raises(SafeModeError, match="active queries"):
            service.suspend_warehouse("TEST_WH")

    @pytest.mark.integration
    def test_real_warehouse_suspension(self):
        """Integration test requiring live Snowflake connection."""
        # This test will only run with: pytest -m integration
        # Requires SNOWFLAKE credentials in .env
        pass
```

### Fixtures

```python
@pytest.fixture
def mock_snowflake_connection():
    """Mock Snowflake connection for unit tests."""
    connection = Mock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = \
        ('VERSION', '1.0.0')
    return connection

@pytest.fixture
def live_snowflake_connection():
    """Live Snowflake connection for integration tests."""
    # Requires environment variables
    return create_snowflake_connection()
```

## Security and Safety Standards

### Security

Validate all inputs and prevent SQL injection:

```python
from pydantic import BaseModel, validator

class WarehouseName(BaseModel):
    name: str

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError("Invalid warehouse name format")
        return v.upper()

class SafeSQLExecutor:
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']

    def execute_read_query(self, sql: str, limit: int = 1000) -> dict:
        validated_sql = self._validate_sql_safety(sql)
        if 'LIMIT' not in validated_sql.upper():
            validated_sql = f"{validated_sql} LIMIT {limit}"
        return self._execute_query(validated_sql)
```

## Configuration

Use Pydantic models for configuration:

```python
from pydantic import BaseModel, Field

class SnowflakeConfig(BaseModel):
    account: str = Field(..., description="Snowflake account identifier")
    user: str = Field(..., description="Snowflake username")
    warehouse: Optional[str] = Field(None, description="Default warehouse")

class IcebreakerConfig(BaseModel):
    snowflake: SnowflakeConfig
    safe_mode: bool = Field(True, description="Enable safe mode operations")
    query_timeout: int = Field(300, description="Query timeout in seconds")
```

## Code Quality

### pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[tool.black]
line-length = 88
target-version = ['py312']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "UP", "B"]

[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-q -m 'not integration'"
markers = [
    "unit: Fast tests without external dependencies (default)",
    "integration: Tests requiring live Snowflake connection",
    "contract: MCP tool contract verification tests",
    "safety: Safety mechanism and security tests",
]
```

## Documentation

Use clear docstrings for all public functions:

```python
def suspend_warehouse(self, name: str, force: bool = False) -> Dict[str, Any]:
    """
    Suspend a Snowflake warehouse with safety checks.

    Args:
        name: Warehouse name to suspend
        force: Bypass safety checks if True

    Returns:
        Dictionary with status, warehouse, and message

    Raises:
        ValidationError: If warehouse name is invalid
        SafeModeError: If safety checks block the operation
    """
```

## Development Workflow

1. Create feature branch from main
2. Write tests first (TDD preferred)
3. Implement functionality following coding standards
4. Run quality checks: `uv run black .`, `uv run ruff check .`, `uv run mypy .`
5. Run tests: `uv run pytest --cov=icebreaker_mcp`
6. Update documentation
7. Create pull request with detailed description
8. Code review and merge to main

## Version Control

- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- **Branches**: `feature/description`, `fix/description`, `hotfix/description`
- **Versioning**: Follow SemVer
- **Management**: Use `uv` for dependency management