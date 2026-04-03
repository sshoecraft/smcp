"""MCP tools for Synapse Admin API server, media, and registration token operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_admin_server_tools(mcp):
    """Register Synapse Admin API server, media, and registration token tools."""

    # ── Server Info ─────────────────────────────────────────────────

    @mcp.tool(
        name="server_version",
        description="Get the Synapse server version via Admin API. Requires server admin privileges."
    )
    async def server_version() -> Dict[str, str]:
        """Get the server version information."""
        result = await mcp.client.get_server_version()
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "server_version": result.get("server_version", ""),
            "python_version": result.get("python_version", ""),
        }

    @mcp.tool(
        name="list_event_reports",
        description="List content violation reports submitted by users via Synapse Admin API. Requires server admin privileges."
    )
    async def list_event_reports(limit: int = 100, offset: int = 0) -> Dict[str, str]:
        """List event reports.

        Args:
            limit: Maximum reports to return (default: 100)
            offset: Pagination offset (default: 0)
        """
        result = await mcp.client.list_event_reports(limit=limit, offset=offset)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "total": str(result.get("total", 0)),
            "event_reports": json.dumps(result.get("event_reports", [])),
        }

    @mcp.tool(
        name="user_media_stats",
        description="Get per-user media usage statistics via Synapse Admin API. Requires server admin privileges."
    )
    async def user_media_stats(order_by: str = "media_length", direction: str = "b",
                               search_term: str = "", limit: int = 100,
                               offset: int = 0) -> Dict[str, str]:
        """Get media usage stats per user.

        Args:
            order_by: Sort by: user_id, displayname, media_length, media_count (default: media_length)
            direction: Sort direction: f=forward, b=backward (default: b)
            search_term: Filter by user ID (optional)
            limit: Maximum results (default: 100)
            offset: Pagination offset (default: 0)
        """
        result = await mcp.client.get_user_media_stats(order_by=order_by, direction=direction,
                                                        search_term=search_term, limit=limit,
                                                        offset=offset)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "total": str(result.get("total", 0)),
            "users": json.dumps(result.get("users", [])),
        }

    # ── Registration Tokens ─────────────────────────────────────────

    @mcp.tool(
        name="create_registration_token",
        description="Create a registration token for new user sign-ups via Synapse Admin API. Requires server admin privileges."
    )
    async def create_registration_token(token: str = "", uses_allowed: int = -1,
                                        expiry_time: int = -1) -> Dict[str, str]:
        """Create a registration token.

        Args:
            token: Custom token string (auto-generated if empty)
            uses_allowed: Number of times the token can be used (-1 for unlimited, default: -1)
            expiry_time: Unix timestamp in milliseconds when token expires (-1 for never, default: -1)
        """
        uses = None if uses_allowed == -1 else uses_allowed
        expiry = None if expiry_time == -1 else expiry_time
        result = await mcp.client.create_registration_token(token=token, uses_allowed=uses,
                                                             expiry_time=expiry)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "token": json.dumps(result)}

    @mcp.tool(
        name="list_registration_tokens",
        description="List registration tokens via Synapse Admin API. Requires server admin privileges."
    )
    async def list_registration_tokens(valid: str = "") -> Dict[str, str]:
        """List registration tokens.

        Args:
            valid: Filter: "true" for valid only, "false" for expired/exhausted only, empty for all (default: empty)
        """
        valid_bool = None
        if valid:
            valid_bool = valid.lower() == "true"
        result = await mcp.client.list_registration_tokens(valid=valid_bool)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "registration_tokens": json.dumps(result.get("registration_tokens", [])),
        }

    @mcp.tool(
        name="revoke_registration_token",
        description="Delete a registration token via Synapse Admin API. Requires server admin privileges."
    )
    async def revoke_registration_token(token: str) -> Dict[str, str]:
        """Delete a registration token so it can no longer be used.

        Args:
            token: The token string to revoke
        """
        result = await mcp.client.revoke_registration_token(token)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true"}

    # ── Media Management ────────────────────────────────────────────

    @mcp.tool(
        name="delete_media",
        description="Delete a specific media item from the server via Synapse Admin API. Requires server admin privileges."
    )
    async def delete_media(server_name: str, media_id: str) -> Dict[str, str]:
        """Delete a media item.

        Args:
            server_name: The server name (e.g., matrix.org)
            media_id: The media ID
        """
        result = await mcp.client.delete_media(server_name, media_id)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "deleted_media": str(result.get("deleted_media", 0))}

    @mcp.tool(
        name="purge_media_cache",
        description="Purge cached remote media older than a given timestamp via Synapse Admin API. Requires server admin privileges."
    )
    async def purge_media_cache(before_ts: int) -> Dict[str, str]:
        """Purge cached remote media.

        Args:
            before_ts: Unix timestamp in milliseconds; remote media cached before this is deleted
        """
        result = await mcp.client.purge_media_cache(before_ts)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "deleted": str(result.get("deleted", 0))}
