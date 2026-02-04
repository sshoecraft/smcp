"""Directory-related MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_directory_tools(mcp):
    """Register directory-related MCP tools."""

    @mcp.tool(
        name="create_directory",
        description="Create a new directory in the specified filesystem"
    )
    async def create_directory(filesystem: str, path: str) -> Dict[str, str]:
        """Create a new directory in the specified filesystem."""
        if mcp.client.read_only:
            return {
                "path": path,
                "success": "false",
                "error": "Cannot create directory in read-only mode"
            }

        try:
            success = await mcp.client.create_directory(filesystem, path)
            return {
                "path": path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to create directory"
            }
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return {
                "path": path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="delete_directory",
        description="Delete a directory from the specified filesystem"
    )
    async def delete_directory(filesystem: str, path: str) -> Dict[str, str]:
        """Delete a directory from the specified filesystem."""
        if mcp.client.read_only:
            return {
                "path": path,
                "success": "false",
                "error": "Cannot delete directory in read-only mode"
            }

        try:
            success = await mcp.client.delete_directory(filesystem, path)
            return {
                "path": path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to delete directory"
            }
        except Exception as e:
            logger.error(f"Error deleting directory {path}: {e}")
            return {
                "path": path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="rename_directory",
        description="Rename/move a directory within the specified filesystem"
    )
    async def rename_directory(filesystem: str, source_path: str, destination_path: str) -> Dict[str, str]:
        """Rename/move a directory within the specified filesystem."""
        if mcp.client.read_only:
            return {
                "path": source_path,
                "success": "false",
                "error": "Cannot rename directory in read-only mode"
            }

        try:
            success = await mcp.client.rename_directory(filesystem, source_path, destination_path)
            return {
                "path": destination_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to rename directory"
            }
        except Exception as e:
            logger.error(f"Error renaming directory {source_path} to {destination_path}: {e}")
            return {
                "path": source_path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="directory_get_paths",
        description="Get all paths under the specified directory"
    )
    async def directory_get_paths(filesystem: str, directory_path: str, recursive: bool = True) -> Dict[str, str]:
        """Get all paths under the specified directory."""
        try:
            paths = await mcp.client.directory_get_paths(filesystem, directory_path, recursive)
            return {
                "path": directory_path,
                "paths": json.dumps(paths),
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error getting paths for directory {directory_path}: {e}")
            return {
                "path": directory_path,
                "paths": "[]",
                "error": str(e)
            }
