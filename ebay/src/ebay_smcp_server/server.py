"""eBay MCP Server with SMCP credential injection."""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake

from ebay_smcp_server.client import EbayClient, EbayConfig
from ebay_smcp_server.tools import register_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the eBay SMCP service."""
    try:
        # Perform SMCP handshake to get credentials
        creds = smcp_handshake()

        # Configure logging level from credentials if provided
        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Create eBay client from credentials
        config = EbayConfig.from_smcp_creds(creds)
        client = EbayClient(config)

        # Initialize MCP server
        mcp = FastMCP("EbaySMCP")
        mcp.client = client

        # Register MCP tools
        register_tools(mcp)

        logger.info("Starting eBay SMCP service")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Error starting eBay SMCP service: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
