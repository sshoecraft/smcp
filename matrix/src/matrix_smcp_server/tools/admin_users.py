"""MCP tools for Synapse Admin API user operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_admin_user_tools(mcp):
    """Register Synapse Admin API user tools."""

    @mcp.tool(
        name="admin_get_user",
        description="Get detailed user account info via Synapse Admin API. Requires server admin privileges."
    )
    async def admin_get_user(user_id: str) -> Dict[str, str]:
        """Get user account details including admin status, creation date, and more.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
        """
        result = await mcp.client.get_user_admin(user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "user": json.dumps(result)}

    @mcp.tool(
        name="admin_modify_user",
        description="Modify a user account via Synapse Admin API. Requires server admin privileges."
    )
    async def admin_modify_user(user_id: str, displayname: str = "",
                                admin: str = "", deactivated: str = "",
                                password: str = "", avatar_url: str = "") -> Dict[str, str]:
        """Modify user account properties.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
            displayname: New display name (optional)
            admin: Set admin status: "true" or "false" (optional)
            deactivated: Set deactivated status: "true" or "false" (optional)
            password: New password (optional)
            avatar_url: New avatar URL (optional)
        """
        admin_bool = None
        if admin:
            admin_bool = admin.lower() == "true"
        deactivated_bool = None
        if deactivated:
            deactivated_bool = deactivated.lower() == "true"

        result = await mcp.client.modify_user(
            user_id, displayname=displayname, admin=admin_bool,
            deactivated=deactivated_bool, password=password, avatar_url=avatar_url,
        )
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "user": json.dumps(result)}

    @mcp.tool(
        name="deactivate_user",
        description="Deactivate a user account via Synapse Admin API. This is difficult to reverse. Requires server admin privileges."
    )
    async def deactivate_user(user_id: str, erase: bool = False) -> Dict[str, str]:
        """Deactivate a user account.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
            erase: Also erase the user's data (messages, etc.) (default: false)
        """
        result = await mcp.client.deactivate_user(user_id, erase=erase)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "id_server_unbind_result": result.get("id_server_unbind_result", "")}

    @mcp.tool(
        name="reset_password",
        description="Reset a user's password via Synapse Admin API. Requires server admin privileges."
    )
    async def reset_password(user_id: str, new_password: str,
                             logout_devices: bool = True) -> Dict[str, str]:
        """Reset a user's password.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
            new_password: The new password
            logout_devices: Log out all existing sessions (default: true)
        """
        result = await mcp.client.reset_password(user_id, new_password, logout_devices=logout_devices)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true"}

    @mcp.tool(
        name="whois_user",
        description="Get active sessions and connection info for a user via Synapse Admin API. Requires server admin privileges."
    )
    async def whois_user(user_id: str) -> Dict[str, str]:
        """Get active session and connection details for a user.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
        """
        result = await mcp.client.whois_user(user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "sessions": json.dumps(result)}

    @mcp.tool(
        name="list_user_devices",
        description="List all devices for a user via Synapse Admin API. Requires server admin privileges."
    )
    async def list_user_devices(user_id: str) -> Dict[str, str]:
        """List all devices registered to a user.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
        """
        result = await mcp.client.list_user_devices(user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "total": str(result.get("total", 0)),
            "devices": json.dumps(result.get("devices", [])),
        }

    @mcp.tool(
        name="delete_user_device",
        description="Delete a specific device for a user via Synapse Admin API. This logs out that device. Requires server admin privileges."
    )
    async def delete_user_device(user_id: str, device_id: str) -> Dict[str, str]:
        """Delete a user's device, logging it out.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
            device_id: The device ID to delete
        """
        result = await mcp.client.delete_user_device(user_id, device_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "user_id": user_id, "device_id": device_id}
