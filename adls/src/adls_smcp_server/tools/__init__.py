"""MCP tools for ADLS2 operations."""

from .filesystems import register_filesystem_tools
from .files import register_file_tools
from .directories import register_directory_tools
from .containers import register_container_tools
from .blobs import register_blob_tools
from .sas import register_sas_tools


def register_all_tools(mcp):
    """Register all MCP tools."""
    register_filesystem_tools(mcp)
    register_file_tools(mcp)
    register_directory_tools(mcp)
    register_container_tools(mcp)
    register_blob_tools(mcp)
    register_sas_tools(mcp)
