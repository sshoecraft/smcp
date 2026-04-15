"""Permission and sharing link MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_permission_tools(mcp):
    """Register permission-related MCP tools."""

    @mcp.tool(
        name="list_permissions",
        description="List permissions on a file or folder in a document library"
    )
    async def list_permissions(drive_id: str, item_path: str) -> Dict[str, str]:
        """List permissions on a drive item."""
        try:
            perms = await mcp.client.list_permissions(drive_id, item_path)
            results = [
                {
                    "id": p.get("id", ""),
                    "roles": p.get("roles", []),
                    "grantedToV2": p.get("grantedToV2", {}),
                    "link": p.get("link", {}),
                }
                for p in perms
            ]
            return {
                "success": "true",
                "path": item_path,
                "permissions": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing permissions for {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "permissions": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="create_sharing_link",
        description="Create a sharing link for a file or folder. link_type: 'view' or 'edit'. scope: 'anonymous', 'organization', or 'users'."
    )
    async def create_sharing_link(
        drive_id: str,
        item_path: str,
        link_type: str = "view",
        scope: str = "anonymous",
        expiration_datetime: str = "",
    ) -> Dict[str, str]:
        """Create a sharing link."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "error": "Cannot create sharing link in read-only mode",
            }

        try:
            result = await mcp.client.create_sharing_link(
                drive_id,
                item_path,
                link_type=link_type,
                scope=scope,
                expiration_datetime=expiration_datetime or None,
            )
            if result:
                link_info = result.get("link", {})
                return {
                    "success": "true",
                    "path": item_path,
                    "url": link_info.get("webUrl", ""),
                    "type": link_info.get("type", ""),
                    "scope": link_info.get("scope", ""),
                    "link": json.dumps(result),
                    "error": "",
                }
            return {
                "success": "false",
                "path": item_path,
                "url": "",
                "error": "Failed to create sharing link",
            }
        except Exception as e:
            logger.error(f"Error creating sharing link for {item_path}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "url": "",
                "error": str(e),
            }

    @mcp.tool(
        name="delete_permission",
        description="Remove a permission from a file or folder in a document library"
    )
    async def delete_permission(
        drive_id: str, item_path: str, permission_id: str
    ) -> Dict[str, str]:
        """Delete a permission."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "path": item_path,
                "permission_id": permission_id,
                "error": "Cannot delete permission in read-only mode",
            }

        try:
            success = await mcp.client.delete_permission(
                drive_id, item_path, permission_id
            )
            return {
                "success": "true" if success else "false",
                "path": item_path,
                "permission_id": permission_id,
                "error": "" if success else "Failed to delete permission",
            }
        except Exception as e:
            logger.error(f"Error deleting permission {permission_id}: {e}")
            return {
                "success": "false",
                "path": item_path,
                "permission_id": permission_id,
                "error": str(e),
            }
