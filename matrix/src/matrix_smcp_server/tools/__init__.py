"""MCP tools for Matrix operations."""

from .messaging import register_messaging_tools
from .rooms import register_room_tools
from .users import register_user_tools
from .admin import register_admin_tools
from .admin_users import register_admin_user_tools
from .admin_server import register_admin_server_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_messaging_tools(mcp)
    register_room_tools(mcp)
    register_user_tools(mcp)
    register_admin_tools(mcp)
    register_admin_user_tools(mcp)
    register_admin_server_tools(mcp)
