"""Icebreaker MCP Server entry point.

Intelligent Snowflake MCP Agent specialized in DataOps and Administration.
Following established patterns from official Snowflake MCP and community references.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .core.config import IcebreakerConfig
from .core.errors import IcebreakerError
from .core.logging import configure_logging, get_logger
from .core.permissions import PermissionManager

# Initialize logging
logger = get_logger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Icebreaker MCP Server - Intelligent Snowflake DataOps Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with environment configuration
  icebreaker-mcp

  # Run with custom config file
  icebreaker-mcp --config config/production.yaml

  # Run in safe mode (default)
  icebreaker-mcp --safe-mode

  # Disable safe mode for full administrative access
  icebreaker-mcp --no-safe-mode
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration YAML file (default: use environment variables)"
    )

    parser.add_argument(
        "--safe-mode",
        action="store_true",
        default=True,
        help="Enable safe mode for administrative operations (default: enabled)"
    )

    parser.add_argument(
        "--no-safe-mode",
        action="store_true",
        help="Disable safe mode for full administrative access"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="MCP transport protocol (default: stdio)"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address for HTTP transport (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port for HTTP transport (default: 9000)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    return parser


def load_config(args: argparse.Namespace) -> IcebreakerConfig:
    """Load configuration from file or environment."""
    try:
        if args.config:
            logger.info("Loading configuration from file", config_file=args.config)
            config = IcebreakerConfig.from_file(args.config)
        else:
            logger.info("Loading configuration from environment variables")
            config = IcebreakerConfig.from_environment()

        # Override with command line arguments
        if args.no_safe_mode:
            config.safe_mode = False
        elif args.safe_mode:
            config.safe_mode = True

        if args.debug:
            config.debug = True

        logger.info(
            "Configuration loaded",
            safe_mode=config.safe_mode,
            debug=config.debug,
            environment=config.environment,
            account=config.snowflake.account
        )

        return config

    except Exception as e:
        logger.error("Failed to load configuration", error=str(e))
        raise IcebreakerError(f"Configuration error: {e}") from e


def create_mcp_server(config: IcebreakerConfig) -> FastMCP:
    """Create and configure the MCP server instance."""
    server = FastMCP(name="icebreaker-mcp")

    # Initialize permission manager
    permission_manager = PermissionManager(config)

    # Load additional configuration files
    try:
        # Load services configuration
        services_config = config.load_services_config("config/services.yaml")
        if services_config:
            logger.info("Loaded services configuration", services=list(services_config.keys()))
            # TODO: Register tools based on services configuration when tools are implemented
            # for service_name, service_config in services_config.items():
            #     if service_config.get('enabled', False):
            #         for tool_name in service_config.get('tools', []):
            #             register_tool(server, tool_name, config, permission_manager)

        # Load permissions configuration
        permissions_config = config.load_permissions_config("config/permissions.yaml")
        if permissions_config:
            logger.info("Loaded permissions configuration", categories=list(permissions_config.keys()))
            # Apply permission configurations
            # Note: Permission system is now integrated via PermissionManager
            logger.info("Permission system initialized with role-based access control")

    except Exception as e:
        logger.warning("Failed to load additional configuration files", error=str(e))

    # Get enabled tools from configuration
    enabled_tools = config.get_enabled_tools()
    if enabled_tools:
        logger.info("Enabled tools from configuration", tools=enabled_tools)
    else:
        logger.info("No tools explicitly enabled - using defaults")

    # TODO: Add tools as they are implemented with permission checks
    # Tier 1: Discovery tools will be added first
    # server.add_tool(list_databases)  # Will be wrapped with permission checks
    # server.add_tool(list_schemas)    # Will be wrapped with permission checks
    # etc.

    # Store permission manager in server context for tool wrappers
    server.permission_manager = permission_manager

    logger.info(
        "MCP server created",
        safe_mode=config.safe_mode,
        query_timeout=config.query_timeout,
        max_results=config.max_query_results,
        enabled_services=len([s for s in config.get_enabled_services().values() if s.enabled]),
        permission_system_enabled=True
    )

    return server


async def main() -> int:
    """Main entry point for the Icebreaker MCP server."""
    try:
        # Parse command line arguments
        parser = create_argument_parser()
        args = parser.parse_args()

        # Configure logging
        configure_logging(
            level=args.log_level,
            format_json=not args.debug,
            enable_colors=args.debug
        )

        logger.info("Starting Icebreaker MCP Server", version="0.1.0")

        # Load configuration
        config = load_config(args)

        # Validate safe mode requirements
        if config.safe_mode:
            logger.info("Safe mode enabled - administrative operations will require explicit confirmation")
        else:
            logger.warning("Safe mode disabled - full administrative access enabled")

        # Create MCP server
        server = create_mcp_server(config)

        # Start server with appropriate transport
        if args.transport == "stdio":
            logger.info("Starting server with stdio transport")
            server.run(transport="stdio")
        elif args.transport in ["http", "sse"]:
            logger.info(
                "Starting server with HTTP transport",
                transport=args.transport,
                host=args.host,
                port=args.port
            )
            server.run(
                transport=args.transport,
                host=args.host,
                port=args.port
            )

        logger.info("Icebreaker MCP Server stopped successfully")
        return 0

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully")
        return 0
    except IcebreakerError as e:
        logger.error("Icebreaker error", error=str(e))
        return 1
    except Exception as e:
        logger.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))