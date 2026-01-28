"""MCP tools for Ecobee operations."""

from .status import register_status_tools
from .settings import register_settings_tools
from .events import register_events_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_status_tools(mcp)
    register_settings_tools(mcp)
    register_events_tools(mcp)
