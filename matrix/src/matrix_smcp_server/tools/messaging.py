"""MCP tools for Matrix messaging operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_messaging_tools(mcp):
    """Register messaging-related MCP tools."""

    @mcp.tool(
        name="send_message",
        description="Send a text message to a Matrix room"
    )
    async def send_message(room_id: str, body: str) -> Dict[str, str]:
        """Send a plain text message to a room.

        Args:
            room_id: The room ID (e.g., !abc123:matrix.org)
            body: The message text
        """
        result = await mcp.client.send_message(room_id, body)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "event_id": result["event_id"], "room_id": result["room_id"]}

    @mcp.tool(
        name="send_html_message",
        description="Send an HTML-formatted message to a Matrix room with a plain text fallback"
    )
    async def send_html_message(room_id: str, body: str, html: str) -> Dict[str, str]:
        """Send an HTML-formatted message to a room.

        Args:
            room_id: The room ID (e.g., !abc123:matrix.org)
            body: Plain text fallback for clients that don't support HTML
            html: The HTML-formatted message body
        """
        result = await mcp.client.send_message(room_id, body, html=html)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "event_id": result["event_id"], "room_id": result["room_id"]}

    @mcp.tool(
        name="read_messages",
        description="Read recent messages from a Matrix room"
    )
    async def read_messages(room_id: str, limit: int = 20) -> Dict[str, str]:
        """Read recent messages from a room.

        Args:
            room_id: The room ID (e.g., !abc123:matrix.org)
            limit: Maximum number of messages to return (default: 20)
        """
        result = await mcp.client.read_messages(room_id, limit=limit)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "room_id": result["room_id"],
            "message_count": str(len(result["messages"])),
            "messages": json.dumps(result["messages"]),
        }

    @mcp.tool(
        name="send_reaction",
        description="Send a reaction (emoji) to a message in a Matrix room"
    )
    async def send_reaction(room_id: str, event_id: str, reaction: str) -> Dict[str, str]:
        """React to a message with an emoji or text.

        Args:
            room_id: The room ID containing the message
            event_id: The event ID of the message to react to
            reaction: The reaction key (e.g., an emoji like a thumbs up)
        """
        result = await mcp.client.send_reaction(room_id, event_id, reaction)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "event_id": result["event_id"], "room_id": result["room_id"]}

    @mcp.tool(
        name="redact_message",
        description="Redact (delete) a message from a Matrix room"
    )
    async def redact_message(room_id: str, event_id: str, reason: str = "") -> Dict[str, str]:
        """Redact a message. The message content is removed but the event remains.

        Args:
            room_id: The room ID containing the message
            event_id: The event ID of the message to redact
            reason: Optional reason for the redaction
        """
        result = await mcp.client.redact_message(room_id, event_id, reason=reason)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "event_id": result["event_id"], "room_id": result["room_id"]}
