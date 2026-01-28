"""MCP tools for HomeKit operations."""

from .generic import register_generic_tools
from .lights import register_light_tools
from .climate import register_climate_tools
from .sensors import register_sensor_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_generic_tools(mcp)
    register_light_tools(mcp)
    register_climate_tools(mcp)
    register_sensor_tools(mcp)
