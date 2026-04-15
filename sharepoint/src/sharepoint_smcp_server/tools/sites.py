"""Site discovery MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_site_tools(mcp):
    """Register site-related MCP tools."""

    @mcp.tool(
        name="list_sites",
        description="List all SharePoint sites accessible to the application"
    )
    async def list_sites() -> Dict[str, str]:
        """List all accessible sites."""
        try:
            sites = await mcp.client.list_sites()
            results = [
                {
                    "id": s.get("id", ""),
                    "name": s.get("name", ""),
                    "displayName": s.get("displayName", ""),
                    "webUrl": s.get("webUrl", ""),
                }
                for s in sites
            ]
            return {
                "success": "true",
                "sites": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing sites: {e}")
            return {
                "success": "false",
                "sites": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="search_sites",
        description="Search for SharePoint sites by keyword"
    )
    async def search_sites(query: str) -> Dict[str, str]:
        """Search sites by keyword."""
        try:
            sites = await mcp.client.search_sites(query)
            results = [
                {
                    "id": s.get("id", ""),
                    "name": s.get("name", ""),
                    "displayName": s.get("displayName", ""),
                    "webUrl": s.get("webUrl", ""),
                }
                for s in sites
            ]
            return {
                "success": "true",
                "sites": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error searching sites: {e}")
            return {
                "success": "false",
                "sites": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="get_site",
        description="Get details of a specific SharePoint site by ID. Uses the configured default site if site_id is empty."
    )
    async def get_site(site_id: str = "") -> Dict[str, str]:
        """Get site details."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            site = await mcp.client.get_site(sid)
            if site:
                return {
                    "success": "true",
                    "site": json.dumps(site),
                    "error": "",
                }
            return {
                "success": "false",
                "site": "{}",
                "error": "Site not found",
            }
        except Exception as e:
            logger.error(f"Error getting site: {e}")
            return {
                "success": "false",
                "site": "{}",
                "error": str(e),
            }

    @mcp.tool(
        name="get_site_by_url",
        description="Get a SharePoint site by its URL (e.g. https://contoso.sharepoint.com/sites/TeamSite)"
    )
    async def get_site_by_url(site_url: str) -> Dict[str, str]:
        """Get a site by its URL."""
        try:
            site = await mcp.client.get_site_by_url(site_url)
            if site:
                return {
                    "success": "true",
                    "site": json.dumps(site),
                    "error": "",
                }
            return {
                "success": "false",
                "site": "{}",
                "error": "Site not found",
            }
        except Exception as e:
            logger.error(f"Error getting site by URL: {e}")
            return {
                "success": "false",
                "site": "{}",
                "error": str(e),
            }
