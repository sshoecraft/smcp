"""MCP tools for Matrix room operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_room_tools(mcp):
    """Register room-related MCP tools."""

    @mcp.tool(
        name="list_rooms",
        description="List all Matrix rooms the authenticated user has joined"
    )
    async def list_rooms() -> Dict[str, str]:
        """List all joined rooms with names, topics, and member counts."""
        result = await mcp.client.list_rooms()
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "room_count": str(len(result["rooms"])),
            "rooms": json.dumps(result["rooms"]),
        }

    @mcp.tool(
        name="join_room",
        description="Join a Matrix room by room ID or alias"
    )
    async def join_room(room_id: str) -> Dict[str, str]:
        """Join a room.

        Args:
            room_id: Room ID (e.g., !abc123:matrix.org) or alias (e.g., #room:matrix.org)
        """
        result = await mcp.client.join_room(room_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "room_id": result["room_id"]}

    @mcp.tool(
        name="leave_room",
        description="Leave a Matrix room"
    )
    async def leave_room(room_id: str) -> Dict[str, str]:
        """Leave a room.

        Args:
            room_id: The room ID to leave
        """
        result = await mcp.client.leave_room(room_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "room_id": result["room_id"], "status": "left"}

    @mcp.tool(
        name="create_room",
        description="Create a new Matrix room"
    )
    async def create_room(name: str = "", topic: str = "", invite: str = "",
                          is_direct: bool = False, public: bool = False) -> Dict[str, str]:
        """Create a new room.

        Args:
            name: Room name (optional)
            topic: Room topic (optional)
            invite: Comma-separated list of user IDs to invite (optional)
            is_direct: Whether this is a direct message room (default: false)
            public: Whether the room is publicly visible (default: false)
        """
        invite_list = [u.strip() for u in invite.split(",") if u.strip()] if invite else []
        result = await mcp.client.create_room(
            name=name, topic=topic, invite=invite_list,
            is_direct=is_direct, public=public,
        )
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "room_id": result["room_id"]}

    @mcp.tool(
        name="set_room_topic",
        description="Set the topic of a Matrix room"
    )
    async def set_room_topic(room_id: str, topic: str) -> Dict[str, str]:
        """Set a room's topic.

        Args:
            room_id: The room ID
            topic: The new topic text
        """
        result = await mcp.client.set_room_topic(room_id, topic)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "event_id": result["event_id"], "room_id": result["room_id"]}

    @mcp.tool(
        name="get_room_state",
        description="Get the state of a Matrix room (name, topic, join rules, creator, etc.)"
    )
    async def get_room_state(room_id: str) -> Dict[str, str]:
        """Get room state information.

        Args:
            room_id: The room ID
        """
        result = await mcp.client.get_room_state(room_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "state": json.dumps(result)}
