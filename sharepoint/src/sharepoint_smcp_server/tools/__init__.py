"""MCP tools for SharePoint operations."""

from .sites import register_site_tools
from .drives import register_drive_tools
from .items import register_item_tools
from .lists import register_list_tools
from .permissions import register_permission_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_site_tools(mcp)
    register_drive_tools(mcp)
    register_item_tools(mcp)
    register_list_tools(mcp)
    register_permission_tools(mcp)
