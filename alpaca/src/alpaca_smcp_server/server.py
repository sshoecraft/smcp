"""Alpaca MCP Server with SMCP credential injection."""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake, check_credentials_schema

from alpaca_smcp_server.client import AlpacaClient, AlpacaConfig
from alpaca_smcp_server.tools import register_tools

CREDENTIALS_SCHEMA = {
    "required": {
        "ALPACA_API_KEY": "Alpaca API key",
        "ALPACA_SECRET_KEY": "Alpaca API secret key"
    },
    "optional": {
        "ALPACA_PAPER": "Use paper trading (default: true)",
        "LOG_LEVEL": "Logging level (default: INFO)"
    }
}


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )


def main() -> None:
    """Main entry point for the Alpaca SMCP server."""
    check_credentials_schema(CREDENTIALS_SCHEMA)

    # Perform SMCP handshake to receive credentials
    creds = smcp_handshake()

    # Setup logging from credentials
    log_level = creds.get("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Alpaca SMCP server")

    # Create client from credentials
    try:
        config = AlpacaConfig.from_smcp_creds(creds)
        client = AlpacaClient(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Create MCP server
    mcp = FastMCP("AlpacaSMCP")

    # Attach client to MCP server for tool access
    mcp.client = client

    # Register tools
    register_tools(mcp)

    logger.info("Alpaca SMCP server ready")

    # Run MCP server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
