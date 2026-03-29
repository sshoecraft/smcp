"""MCP tools for Matrix user operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_user_tools(mcp):
    """Register user-related MCP tools."""

    @mcp.tool(
        name="invite_user",
        description="Invite a user to a Matrix room"
    )
    async def invite_user(room_id: str, user_id: str) -> Dict[str, str]:
        """Invite a user to a room.

        Args:
            room_id: The room ID to invite the user to
            user_id: The user ID to invite (e.g., @user:matrix.org)
        """
        result = await mcp.client.invite_user(room_id, user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "room_id": result["room_id"],
            "user_id": result["user_id"],
            "status": "invited",
        }

    @mcp.tool(
        name="get_room_members",
        description="Get the list of members in a Matrix room"
    )
    async def get_room_members(room_id: str) -> Dict[str, str]:
        """Get all members of a room.

        Args:
            room_id: The room ID
        """
        result = await mcp.client.get_room_members(room_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "room_id": result["room_id"],
            "member_count": str(len(result["members"])),
            "members": json.dumps(result["members"]),
        }

    @mcp.tool(
        name="get_user_profile",
        description="Get a Matrix user's profile (display name and avatar)"
    )
    async def get_user_profile(user_id: str) -> Dict[str, str]:
        """Get a user's profile information.

        Args:
            user_id: The user ID (e.g., @user:matrix.org)
        """
        result = await mcp.client.get_user_profile(user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "user_id": result["user_id"],
            "display_name": result["display_name"],
            "avatar_url": result["avatar_url"],
        }

    @mcp.tool(
        name="set_display_name",
        description="Set the display name for the authenticated Matrix user"
    )
    async def set_display_name(display_name: str) -> Dict[str, str]:
        """Set the authenticated user's display name.

        Args:
            display_name: The new display name
        """
        result = await mcp.client.set_display_name(display_name)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "display_name": result["display_name"], "status": "updated"}
