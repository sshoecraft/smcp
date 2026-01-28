"""Alpaca MCP Server with SMCP credential injection."""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake

from alpaca_smcp_server.client import AlpacaClient, AlpacaConfig
from alpaca_smcp_server.tools import register_tools


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
