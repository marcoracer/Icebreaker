# Icebreaker MCP Server

Intelligent Snowflake MCP Agent specialized in DataOps and Administration.

## Overview

Icebreaker is an advanced Model Context Protocol (MCP) server that provides intelligent Snowflake database management capabilities. It combines the reliability of the official Snowflake Labs MCP implementation with community best practices and intelligent automation features.

## Features

### 🏗️ Foundation Layer (Built on Official & Community Best Practices)
- **Robust Connection Management**: Singleton pattern with health monitoring and background refresh
- **Multi-Format Configuration**: Support for both YAML and TOML configuration files
- **Advanced SQL Validation**: Multi-pattern injection detection and comprehensive write operation analysis
- **Production-Ready Testing**: Explicit marker-based separation between unit and integration tests

### 🛡️ Safety & Governance (Icebreaker Intelligence)
- **Multi-Layer Safety Validation**: Business rule enforcement and pre-operation impact assessment
- **Comprehensive Audit Logging**: Immutable audit trails with detailed operation context
- **Approval Workflows**: Configurable approval chains for high-risk administrative operations
- **Rollback Capabilities**: Automatic rollback plan generation for destructive operations

### 📊 DataOps Automation (Intelligent Operations)
- **Warehouse Management**: Intelligent suspension, resizing, and load optimization
- **User Administration**: Safe user lifecycle management with role hierarchy analysis
- **Query Management**: Advanced query diagnostics and performance optimization
- **Pipeline Orchestration**: Automated data pipeline monitoring and self-healing

### 🚀 Intelligence & Analytics (AI-Powered Insights)
- **Performance Diagnostics**: Comprehensive query performance analysis with bottleneck identification
- **Cost Optimization**: Financial operations analysis with cost-saving recommendations
- **Security Intelligence**: Advanced access pattern analysis and threat detection
- **Predictive Analytics**: Resource usage forecasting and capacity planning

## Quick Start

### Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: `uv` (recommended) or pip
- **Snowflake Account**: With appropriate permissions for intended operations

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd icebreaker-mcp

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Snowflake credentials** in `.env`:
   ```bash
   # Required
   SNOWFLAKE_ACCOUNT=your_account_identifier
   SNOWFLAKE_USER=your_username
   SNOWFLAKE_ROLE=your_default_role
   SNOWFLAKE_WAREHOUSE=your_default_warehouse

   # Choose authentication method
   SNOWFLAKE_PASSWORD=your_password
   # OR
   SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/private_key.pem
   # OR
   SNOWFLAKE_AUTHENTICATOR=externalbrowser
   ```

### Running the Server

```bash
# Run with stdio transport (default)
icebreaker-mcp

# Run with HTTP transport
icebreaker-mcp --transport http --host 0.0.0.0 --port 9000

# Run with custom configuration
icebreaker-mcp --config config/production.yaml

# Run with safe mode disabled (full administrative access)
icebreaker-mcp --no-safe-mode
```

## Development

### Project Structure

```
icebreaker-mcp/
├── src/icebreaker/              # Main package
│   ├── core/                   # Core infrastructure
│   │   ├── config.py          # Configuration management
│   │   ├── errors.py          # Custom error classes
│   │   └── ...                # Connection, logging, safety
│   ├── services/              # Business logic layer
│   │   ├── discovery_service.py      # Tier 1: Data discovery
│   │   ├── operational_service.py     # Tier 2: DataOps operations
│   │   ├── intelligence_service.py    # Tier 4: AI-powered insights
│   │   └── ...
│   ├── tools/                 # MCP tool implementations
│   └── server.py              # FastMCP server entry point
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests (fast)
│   ├── integration/          # Integration tests (requires Snowflake)
│   └── conftest.py           # Test configuration
├── docs/                     # Documentation
├── pyproject.toml           # Project configuration
└── .env.example             # Environment template
```

### Testing

```bash
# Run unit tests only (default - fast)
pytest

# Run integration tests (requires Snowflake credentials)
pytest -m integration

# Run specific test categories
pytest -m "unit or contract"
pytest -m "safety"

# Run all tests
pytest -m "unit or integration or contract or safety"

# Run with coverage
pytest --cov=icebreaker
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .

# Run all quality checks
uv run black . && uv run ruff check . && uv run mypy . && pytest -m unit
```

## Configuration

### Environment Variables

Key configuration options:

- **ICEBREAKER_SAFE_MODE**: Enable safety checks for administrative operations (default: true)
- **ICEBREAKER_QUERY_TIMEOUT**: Query timeout in seconds (default: 300)
- **ICEBREAKER_MAX_QUERY_RESULTS**: Maximum results per query (default: 10000)
- **ICEBREAKER_AUDIT_LOGGING**: Enable comprehensive audit logging (default: true)
- **ICEBREAKER_DEBUG**: Enable debug mode for detailed logging (default: false)

### Configuration Files

You can also use YAML configuration files:

```yaml
# config/production.yaml
snowflake:
  account: "your_account"
  user: "your_user"
  role: "your_role"
  warehouse: "your_warehouse"
  auth_type: "private_key"
  private_key_path: "/path/to/key.pem"

safe_mode: true
query_timeout: 300
max_query_results: 10000
audit_logging: true
environment: "production"
```

## Architecture

Icebreaker follows a layered architecture:

1. **Foundation Layer**: Reuses official Snowflake MCP core components
2. **Community Enhancement Layer**: Integrates best practices from community implementations
3. **Safety Layer**: Multi-layer validation and governance
4. **Intelligence Layer**: AI-powered analytics and automation

## Security

- **SQL Injection Protection**: Multi-pattern detection beyond basic keyword matching
- **Write Operation Detection**: Comprehensive analysis including CTE write detection
- **Connection Security**: Support for multiple authentication methods including private key
- **Audit Logging**: Complete audit trail for all operations
- **Safe Mode**: Configurable safety restrictions for administrative operations

## Roadmap

- **Phase 1** (Current): Foundation & Tier 1 - Data discovery and basic queries
- **Phase 2**: Tier 2 - Operational Management (DataOps)
- **Phase 3**: Tier 3 - Data Engineering & Movement
- **Phase 4**: Tier 4 - High-Level Intelligent Actions

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for detailed implementation roadmap.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the [coding standards](docs/CODING_STANDARDS.md)
4. Run tests and quality checks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Snowflake Labs**: For the official MCP implementation providing the foundation
- **Community Contributors**: For the excellent reference implementations that informed best practices
- **diasv_mcp**: For exemplary code structure and testing patterns
- **snowflake-mcp-server**: For advanced connection management patterns
- **mcp-snowflake-server3**: For sophisticated SQL analysis capabilities

## Support

For questions, issues, or contributions:

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/your-org/icebreaker-mcp/issues)
- 💬 [Discussions](https://github.com/your-org/icebreaker-mcp/discussions)
