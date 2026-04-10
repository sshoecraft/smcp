"""Blob container MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_container_tools(mcp):
    """Register blob container related MCP tools."""

    @mcp.tool(
        name="list_containers",
        description="List all blob containers in the storage account"
    )
    async def list_containers() -> Dict[str, str]:
        """List all blob containers in the storage account."""
        try:
            containers = await mcp.client.list_containers()
            return {
                "success": "true",
                "containers": json.dumps(containers),
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return {
                "success": "false",
                "containers": "[]",
                "error": str(e)
            }

    @mcp.tool(
        name="create_container",
        description="Create a new blob container in the storage account"
    )
    async def create_container(name: str) -> Dict[str, str]:
        """Create a new blob container in the storage account."""
        if mcp.client.read_only:
            return {
                "name": name,
                "success": "false",
                "error": "Cannot create container in read-only mode"
            }

        try:
            success = await mcp.client.create_blob_container(name)
            return {
                "name": name,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to create container"
            }
        except Exception as e:
            logger.error(f"Error creating container {name}: {e}")
            return {
                "name": name,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="delete_container",
        description="Delete a blob container from the storage account"
    )
    async def delete_container(name: str) -> Dict[str, str]:
        """Delete a blob container from the storage account."""
        if mcp.client.read_only:
            return {
                "name": name,
                "success": "false",
                "error": "Cannot delete container in read-only mode"
            }

        try:
            success = await mcp.client.delete_blob_container(name)
            return {
                "name": name,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to delete container"
            }
        except Exception as e:
            logger.error(f"Error deleting container {name}: {e}")
            return {
                "name": name,
                "success": "false",
                "error": str(e)
            }
