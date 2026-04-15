"""Document library (drive) MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_drive_tools(mcp):
    """Register drive-related MCP tools."""

    @mcp.tool(
        name="list_drives",
        description="List document libraries (drives) in a SharePoint site. Uses the configured default site if site_id is empty."
    )
    async def list_drives(site_id: str = "") -> Dict[str, str]:
        """List drives in a site."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            drives = await mcp.client.list_drives(sid)
            results = [
                {
                    "id": d.get("id", ""),
                    "name": d.get("name", ""),
                    "description": d.get("description", ""),
                    "webUrl": d.get("webUrl", ""),
                    "driveType": d.get("driveType", ""),
                }
                for d in drives
            ]
            return {
                "success": "true",
                "drives": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing drives: {e}")
            return {
                "success": "false",
                "drives": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="get_drive",
        description="Get details of a specific document library (drive) by its ID"
    )
    async def get_drive(drive_id: str) -> Dict[str, str]:
        """Get drive details."""
        try:
            drive = await mcp.client.get_drive(drive_id)
            if drive:
                return {
                    "success": "true",
                    "drive": json.dumps(drive),
                    "error": "",
                }
            return {
                "success": "false",
                "drive": "{}",
                "error": "Drive not found",
            }
        except Exception as e:
            logger.error(f"Error getting drive: {e}")
            return {
                "success": "false",
                "drive": "{}",
                "error": str(e),
            }
