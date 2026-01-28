"""MCP tool definitions for MQTT operations."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all MQTT tools with the MCP server."""

    @mcp.tool(
        name="publish",
        description="Publish a message to an MQTT topic"
    )
    async def publish(topic: str, message: str, retain: bool = False) -> Dict[str, str]:
        """Publish a message to an MQTT topic.

        Args:
            topic: The MQTT topic to publish to
            message: The message payload (string)
            retain: Whether to retain the message on the broker

        Returns:
            Dict with success status or error
        """
        result = await mcp.client.publish(topic, message, retain)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "topic": result["topic"], "retain": result["retain"]}

    @mcp.tool(
        name="subscribe",
        description="Subscribe to an MQTT topic pattern and receive messages"
    )
    async def subscribe(topic: str, timeout: float = 2.0) -> Dict[str, str]:
        """Subscribe to a topic and collect messages for a duration.

        Args:
            topic: Topic pattern to subscribe to (supports + and # wildcards)
            timeout: How long to wait for messages in seconds (default: 2.0)

        Returns:
            Dict with list of messages received
        """
        messages = await mcp.client.subscribe(topic, timeout)
        if messages and "error" in messages[0]:
            return {"success": "false", "error": messages[0]["error"]}
        return {
            "success": "true",
            "message_count": str(len(messages)),
            "messages": json.dumps(messages)
        }

    @mcp.tool(
        name="get_retained",
        description="Get retained messages from an MQTT topic pattern"
    )
    async def get_retained(topic: str, timeout: float = 1.0) -> Dict[str, str]:
        """Get retained messages from a topic pattern.

        Subscribes briefly to collect retained messages, then unsubscribes.

        Args:
            topic: Topic pattern (supports + and # wildcards)
            timeout: How long to wait for retained messages in seconds (default: 1.0)

        Returns:
            Dict with list of retained messages found
        """
        messages = await mcp.client.get_retained(topic, timeout)
        if messages and "error" in messages[0]:
            return {"success": "false", "error": messages[0]["error"]}
        return {
            "success": "true",
            "message_count": str(len(messages)),
            "messages": json.dumps(messages)
        }

    @mcp.tool(
        name="unsubscribe",
        description="Unsubscribe from an MQTT topic"
    )
    async def unsubscribe(topic: str) -> Dict[str, str]:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from

        Returns:
            Dict with success status
        """
        result = await mcp.client.unsubscribe(topic)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {"success": "true", "topic": result["topic"]}
