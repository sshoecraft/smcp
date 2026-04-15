"""File and folder (drive item) MCP tools."""

import base64
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_item_tools(mcp):
    """Register drive item (file/folder) MCP tools."""

    @mcp.tool(
        name="list_children",
        description="List files and folders at a path in a document library. Use item_path='/' for the root."
    )
    async def list_children(drive_id: str, item_path: str = "/") -> Dict[str, str]:
        """List children at a path."""
        try:
            items = await mcp.client.list_children(drive_id, item_path)
            results = [
                {
                    "id": i.get("id", ""),
                    "name": i.get("name", ""),
                    "size": str(i.get("size", 0)),
                    "lastModifiedDateTime": i.get("lastModifiedDateTime", ""),
                    "type": "folder" if "folder" in i else "file",
                    "webUrl": i.get("webUrl", ""),
                }
                for i in items
            ]
            return {
                "success": "true",
                "path": item_path,
                "items": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing children at {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "items": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="get_item",
        description="Get properties of a file or folder in a document library by its path"
    )
    async def get_item(drive_id: str, item_path: str) -> Dict[str, str]:
        """Get item properties."""
        try:
            item = await mcp.client.get_item(drive_id, item_path)
            if item:
                return {
                    "success": "true",
                    "item": json.dumps(item),
                    "error": "",
                }
            return {
                "success": "false",
                "item": "{}",
                "error": "Item not found",
            }
        except Exception as e:
            logger.error(f"Error getting item {item_path}: {e}")
            return {
                "success": "false",
                "item": "{}",
                "error": str(e),
            }

    @mcp.tool(
        name="search_items",
        description="Search for files and folders within a document library by keyword"
    )
    async def search_items(drive_id: str, query: str) -> Dict[str, str]:
        """Search items in a drive."""
        try:
            items = await mcp.client.search_items(drive_id, query)
            results = [
                {
                    "id": i.get("id", ""),
                    "name": i.get("name", ""),
                    "size": str(i.get("size", 0)),
                    "lastModifiedDateTime": i.get("lastModifiedDateTime", ""),
                    "type": "folder" if "folder" in i else "file",
                    "webUrl": i.get("webUrl", ""),
                }
                for i in items
            ]
            return {
                "success": "true",
                "query": query,
                "items": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error searching items: {e}")
            return {
                "success": "false",
                "query": query,
                "items": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="download_item_content",
        description="Download file content from a document library. Returns text (encoding='utf-8') or base64 (encoding='base64')."
    )
    async def download_item_content(
        drive_id: str, item_path: str, encoding: str = "utf-8"
    ) -> Dict[str, str]:
        """Download file content."""
        try:
            data = await mcp.client.download_item_content(drive_id, item_path)
            if data is None:
                return {
                    "success": "false",
                    "path": item_path,
                    "content": "",
                    "error": "Failed to download file",
                }
            if encoding == "base64":
                content = base64.b64encode(data).decode("ascii")
            elif encoding == "utf-8":
                content = data.decode("utf-8")
            else:
                return {
                    "success": "false",
                    "path": item_path,
                    "content": "",
                    "error": f"Unsupported encoding: {encoding}. Use 'utf-8' or 'base64'.",
                }
            return {
                "success": "true",
                "path": item_path,
                "content": content,
                "size": str(len(data)),
                "error": "",
            }
        except UnicodeDecodeError:
            return {
                "success": "false",
                "path": item_path,
                "content": "",
                "error": "File is binary. Use encoding='base64' to download binary files.",
            }
        except Exception as e:
            logger.error(f"Error downloading {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "content": "",
                "error": str(e),
            }

    @mcp.tool(
        name="upload_item_content",
        description="Upload text or base64-encoded content as a file to a document library (max 4MB). Use encoding='utf-8' for text, 'base64' for binary."
    )
    async def upload_item_content(
        drive_id: str, item_path: str, content: str, encoding: str = "utf-8"
    ) -> Dict[str, str]:
        """Upload content as a file."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "error": "Cannot upload in read-only mode",
            }

        try:
            if encoding == "base64":
                data = base64.b64decode(content)
            elif encoding == "utf-8":
                data = content.encode("utf-8")
            else:
                return {
                    "success": "false",
                    "path": item_path,
                    "error": f"Unsupported encoding: {encoding}. Use 'utf-8' or 'base64'.",
                }

            result = await mcp.client.upload_item_content(drive_id, item_path, data)
            if result:
                return {
                    "success": "true",
                    "path": item_path,
                    "id": result.get("id", ""),
                    "size": str(result.get("size", len(data))),
                    "error": "",
                }
            return {
                "success": "false",
                "path": item_path,
                "error": "Failed to upload file",
            }
        except Exception as e:
            logger.error(f"Error uploading to {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "error": str(e),
            }

    @mcp.tool(
        name="create_folder",
        description="Create a new folder in a document library"
    )
    async def create_folder(
        drive_id: str, parent_path: str, folder_name: str
    ) -> Dict[str, str]:
        """Create a folder."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "folder_name": folder_name,
                "error": "Cannot create folder in read-only mode",
            }

        try:
            result = await mcp.client.create_folder(drive_id, parent_path, folder_name)
            if result:
                return {
                    "success": "true",
                    "folder_name": folder_name,
                    "id": result.get("id", ""),
                    "webUrl": result.get("webUrl", ""),
                    "error": "",
                }
            return {
                "success": "false",
                "folder_name": folder_name,
                "error": "Failed to create folder",
            }
        except Exception as e:
            logger.error(f"Error creating folder {folder_name}: {e}")
            return {
                "success": "false",
                "folder_name": folder_name,
                "error": str(e),
            }

    @mcp.tool(
        name="delete_item",
        description="Delete a file or folder from a document library"
    )
    async def delete_item(drive_id: str, item_path: str) -> Dict[str, str]:
        """Delete a file or folder."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "error": "Cannot delete in read-only mode",
            }

        try:
            success = await mcp.client.delete_item(drive_id, item_path)
            return {
                "success": "true" if success else "false",
                "path": item_path,
                "error": "" if success else "Failed to delete item",
            }
        except Exception as e:
            logger.error(f"Error deleting {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "error": str(e),
            }

    @mcp.tool(
        name="move_item",
        description="Move and/or rename a file or folder. Provide new_name to rename, destination_parent_path to move, or both."
    )
    async def move_item(
        drive_id: str,
        item_path: str,
        new_name: str = "",
        destination_parent_path: str = "",
    ) -> Dict[str, str]:
        """Move/rename a file or folder."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "error": "Cannot move in read-only mode",
            }

        try:
            result = await mcp.client.move_item(
                drive_id,
                item_path,
                new_name=new_name or None,
                destination_parent_path=destination_parent_path or None,
            )
            if result:
                return {
                    "success": "true",
                    "path": item_path,
                    "new_name": result.get("name", ""),
                    "id": result.get("id", ""),
                    "error": "",
                }
            return {
                "success": "false",
                "path": item_path,
                "error": "Failed to move item",
            }
        except Exception as e:
            logger.error(f"Error moving {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "error": str(e),
            }

    @mcp.tool(
        name="copy_item",
        description="Copy a file or folder to a new location in the same document library"
    )
    async def copy_item(
        drive_id: str,
        item_path: str,
        destination_parent_path: str,
        new_name: str = "",
    ) -> Dict[str, str]:
        """Copy a file or folder."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "error": "Cannot copy in read-only mode",
            }

        try:
            success = await mcp.client.copy_item(
                drive_id,
                item_path,
                destination_parent_path,
                new_name=new_name or None,
            )
            return {
                "success": "true" if success else "false",
                "path": item_path,
                "destination": destination_parent_path,
                "error": "" if success else "Failed to copy item",
            }
        except Exception as e:
            logger.error(f"Error copying {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "destination": destination_parent_path,
                "error": str(e),
            }
