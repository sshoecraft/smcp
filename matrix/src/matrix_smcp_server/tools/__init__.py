"""MCP tools for Matrix operations."""

from .messaging import register_messaging_tools
from .rooms import register_room_tools
from .users import register_user_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_messaging_tools(mcp)
    register_room_tools(mcp)
    register_user_tools(mcp)
