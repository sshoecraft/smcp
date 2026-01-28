"""MQTT MCP Server with SMCP credential injection."""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake

from mqtt_smcp_server.client import MQTTClient, MQTTConfig
from mqtt_smcp_server.tools import register_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MQTT SMCP service."""
    try:
        # Perform SMCP handshake to get credentials
        creds = smcp_handshake()

        # Configure logging level from credentials if provided
        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Create MQTT client from credentials
        config = MQTTConfig.from_smcp_creds(creds)
        client = MQTTClient(config)

        # Connect to broker
        client.connect()

        # Create MCP server
        mcp = FastMCP("MQTTSMCP")
        mcp.client = client

        # Register tools
        register_tools(mcp)

        logger.info(f"Starting MQTT SMCP service connected to {config.broker}:{config.port}")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Error starting MQTT SMCP service: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
