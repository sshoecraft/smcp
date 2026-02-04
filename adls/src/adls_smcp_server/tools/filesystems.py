"""Filesystem-related MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_filesystem_tools(mcp):
    """Register filesystem related MCP tools."""

    @mcp.tool(
        name="list_filesystems",
        description="List all filesystems in the storage account"
    )
    async def list_filesystems() -> Dict[str, str]:
        """List all filesystems in the storage account."""
        try:
            fs = await mcp.client.list_filesystems()
            return {
                "success": "true",
                "filesystems": json.dumps(fs),
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error listing filesystems: {e}")
            return {
                "success": "false",
                "filesystems": "[]",
                "error": str(e)
            }

    @mcp.tool(
        name="create_filesystem",
        description="Create a new ADLS2 filesystem (container)"
    )
    async def create_filesystem(name: str) -> Dict[str, str]:
        """Create a new filesystem in the storage account."""
        if mcp.client.read_only:
            return {
                "name": name,
                "success": "false",
                "error": "Cannot create filesystem in read-only mode"
            }

        try:
            success = await mcp.client.create_container(name)
            return {
                "name": name,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to create filesystem"
            }
        except Exception as e:
            logger.error(f"Error creating filesystem {name}: {e}")
            return {
                "name": name,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="delete_filesystem",
        description="Delete an ADLS2 filesystem"
    )
    async def delete_filesystem(name: str) -> Dict[str, str]:
        """Delete a filesystem from the storage account."""
        if mcp.client.read_only:
            return {
                "name": name,
                "success": "false",
                "error": "Cannot delete filesystem in read-only mode"
            }

        try:
            success = await mcp.client.delete_filesystem(name)
            return {
                "name": name,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to delete filesystem"
            }
        except Exception as e:
            logger.error(f"Error deleting filesystem {name}: {e}")
            return {
                "name": name,
                "success": "false",
                "error": str(e)
            }
