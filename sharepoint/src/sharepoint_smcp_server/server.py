"""SharePoint MCP Server with SMCP credential injection."""

import asyncio
import logging
import sys

from mcp.server.fastmcp import FastMCP
from importlib.metadata import version as pkg_version

from smcp import handshake as smcp_handshake, check_credentials_schema

from sharepoint_smcp_server.client import SharePointClient, SharePointConfig
from sharepoint_smcp_server.tools import register_all_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = {
    "required": {
        "TENANT_ID": "Azure AD tenant ID",
        "CLIENT_ID": "Azure AD application (client) ID",
    },
    "optional": {
        "CLIENT_SECRET": "Azure AD client secret (service principal auth)",
        "USERNAME": "Azure AD username/email (username+password auth)",
        "PASSWORD": "Azure AD password (username+password auth)",
        "SITE_URL": "SharePoint site URL (e.g. https://contoso.sharepoint.com/sites/TeamSite)",
        "READ_ONLY_MODE": "Set to 'true' to disable write operations (default: 'false')",
        "LOG_LEVEL": "Logging level (default: 'INFO')",
    }
}


def main():
    """Main entry point for the SharePoint SMCP service."""
    check_credentials_schema(CREDENTIALS_SCHEMA)

    try:
        # Perform SMCP handshake to get credentials
        creds = smcp_handshake()

        # Configure logging level from credentials if provided
        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Create SharePoint client from credentials
        config = SharePointConfig.from_smcp_creds(creds)
        client = SharePointClient(config)

        # Resolve SITE_URL to site_id if configured
        asyncio.run(client.initialize())

        # Initialize MCP server
        mcp = FastMCP("SharePointSMCP")
        mcp.client = client

        # Register version tool
        @mcp.tool(
            name="sharepoint_version",
            description="Return the running version of the SharePoint SMCP server"
        )
        async def sharepoint_version() -> dict:
            return {"version": pkg_version("sharepoint-smcp-server")}

        # Register all MCP tools
        register_all_tools(mcp)

        logger.info("Starting SharePoint SMCP service")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Error starting SharePoint SMCP service: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
