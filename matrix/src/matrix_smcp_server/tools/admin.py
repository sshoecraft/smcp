"""MCP tools for Synapse Admin API room operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_admin_tools(mcp):
    """Register Synapse Admin API room tools."""

    @mcp.tool(
        name="destroy_room",
        description="Permanently destroy a Matrix room using the Synapse Admin API. Requires server admin privileges. This is irreversible."
    )
    async def destroy_room(room_id: str, block: bool = False,
                           purge: bool = True, force_purge: bool = False) -> Dict[str, str]:
        """Destroy a room permanently.

        Args:
            room_id: The room ID to destroy (e.g., !abc123:matrix.org)
            block: Block the room to prevent users from joining again (default: false)
            purge: Remove all room data from the database (default: true)
            force_purge: Force purge even if there are errors (default: false)
        """
        result = await mcp.client.destroy_room(room_id, block=block, purge=purge, force_purge=force_purge)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "delete_id": result["delete_id"], "room_id": result["room_id"]}

    @mcp.tool(
        name="admin_list_rooms",
        description="List all rooms on the server via Synapse Admin API. Requires server admin privileges."
    )
    async def admin_list_rooms(order_by: str = "name", direction: str = "f",
                               search_term: str = "", limit: int = 100,
                               offset: int = 0) -> Dict[str, str]:
        """List all rooms on the server.

        Args:
            order_by: Sort field: name, canonical_alias, joined_members, joined_local_members, version, creator, encryption, federatable, public, join_rules, guest_access, history_visibility, state_events (default: name)
            direction: Sort direction: f=forward, b=backward (default: f)
            search_term: Filter rooms by name (optional)
            limit: Maximum number of rooms to return (default: 100)
            offset: Pagination offset (default: 0)
        """
        result = await mcp.client.list_all_rooms(order_by=order_by, direction=direction,
                                                  search_term=search_term, limit=limit, offset=offset)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "total_rooms": str(result.get("total_rooms", 0)),
            "rooms": json.dumps(result.get("rooms", [])),
        }

    @mcp.tool(
        name="admin_get_room_details",
        description="Get detailed information about a room via Synapse Admin API. Requires server admin privileges."
    )
    async def admin_get_room_details(room_id: str) -> Dict[str, str]:
        """Get detailed room information including stats not available via the client API.

        Args:
            room_id: The room ID
        """
        result = await mcp.client.get_room_details(room_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "room": json.dumps(result)}

    @mcp.tool(
        name="block_room",
        description="Block or unblock a room via Synapse Admin API. Blocked rooms cannot be joined. Requires server admin privileges."
    )
    async def block_room(room_id: str, block: bool = True) -> Dict[str, str]:
        """Block or unblock a room.

        Args:
            room_id: The room ID
            block: True to block, false to unblock (default: true)
        """
        result = await mcp.client.block_room(room_id, block=block)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "block": str(result.get("block", block)).lower()}

    @mcp.tool(
        name="make_room_admin",
        description="Grant a user room admin (power level 100) in a room via Synapse Admin API. Requires server admin privileges."
    )
    async def make_room_admin(room_id: str, user_id: str = "") -> Dict[str, str]:
        """Grant admin privileges in a room.

        Args:
            room_id: The room ID
            user_id: User to make admin (defaults to the authenticated user if empty)
        """
        result = await mcp.client.make_room_admin(room_id, user_id=user_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "room_id": room_id}

    @mcp.tool(
        name="purge_history",
        description="Purge room history up to a timestamp via Synapse Admin API. Messages older than the timestamp are removed. Requires server admin privileges."
    )
    async def purge_history(room_id: str, purge_up_to_ts: int) -> Dict[str, str]:
        """Purge room message history.

        Args:
            room_id: The room ID
            purge_up_to_ts: Unix timestamp in milliseconds; messages older than this are purged
        """
        result = await mcp.client.purge_history(room_id, purge_up_to_ts=purge_up_to_ts)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "purge_id": result.get("purge_id", "")}
