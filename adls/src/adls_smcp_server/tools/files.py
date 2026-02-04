"""File-related MCP tools."""

import json
import logging
from typing import Dict, Union

logger = logging.getLogger(__name__)


def register_file_tools(mcp):
    """Register file-related MCP tools."""

    @mcp.tool(
        name="upload_file",
        description="Upload a file to ADLS2"
    )
    async def upload_file(upload_file: str, filesystem: str, destination: str) -> Dict[str, str]:
        """Upload a file to ADLS2."""
        if mcp.client.read_only:
            return {
                "source": upload_file,
                "destination": destination,
                "success": "false",
                "error": "Cannot upload file in read-only mode"
            }

        try:
            success = await mcp.client.upload_file(upload_file, filesystem, destination)
            return {
                "source": upload_file,
                "destination": destination,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to upload file"
            }
        except Exception as e:
            logger.error(f"Error uploading file {upload_file} to {destination}: {e}")
            return {
                "source": upload_file,
                "destination": destination,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="download_file",
        description="Download a file from ADLS2"
    )
    async def download_file(filesystem: str, source: str, download_path: str) -> Dict[str, str]:
        """Download a file from ADLS2."""
        try:
            success = await mcp.client.download_file(filesystem, source, download_path)
            return {
                "source": source,
                "destination": download_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to download file"
            }
        except Exception as e:
            logger.error(f"Error downloading file {source} to {download_path}: {e}")
            return {
                "source": source,
                "destination": download_path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="file_exists",
        description="Check if a file exists in the specified filesystem"
    )
    async def file_exists(filesystem: str, file_path: str) -> Dict[str, str]:
        """Check if a file exists in the specified filesystem."""
        try:
            exists = await mcp.client.file_exists(filesystem, file_path)
            return {
                "path": file_path,
                "exists": "true" if exists else "false",
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return {
                "path": file_path,
                "exists": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="rename_file",
        description="Rename/move a file within the specified filesystem"
    )
    async def rename_file(filesystem: str, source_path: str, destination_path: str) -> Dict[str, str]:
        """Rename/move a file within the specified filesystem."""
        if mcp.client.read_only:
            return {
                "source": source_path,
                "destination": destination_path,
                "success": "false",
                "error": "Cannot rename file in read-only mode"
            }

        try:
            success = await mcp.client.rename_file(filesystem, source_path, destination_path)
            return {
                "source": source_path,
                "destination": destination_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to rename file"
            }
        except Exception as e:
            logger.error(f"Error renaming file {source_path} to {destination_path}: {e}")
            return {
                "source": source_path,
                "destination": destination_path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="get_file_properties",
        description="Get properties of a file in the specified filesystem"
    )
    async def get_file_properties(filesystem: str, file_path: str) -> Dict[str, str]:
        """Get properties of a file in the specified filesystem."""
        try:
            properties = await mcp.client.get_file_properties(filesystem, file_path)
            if properties is not None:
                return {
                    "path": file_path,
                    "properties": json.dumps(properties),
                    "success": "true",
                    "error": ""
                }
            else:
                return {
                    "path": file_path,
                    "properties": "{}",
                    "success": "false",
                    "error": "Failed to get file properties"
                }
        except Exception as e:
            logger.error(f"Error getting properties for file {file_path}: {e}")
            return {
                "path": file_path,
                "properties": "{}",
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="get_file_metadata",
        description="Get metadata of a file in the specified filesystem"
    )
    async def get_file_metadata(filesystem: str, file_path: str) -> Dict[str, str]:
        """Get metadata of a file in the specified filesystem."""
        try:
            metadata = await mcp.client.get_file_metadata(filesystem, file_path)
            if metadata is not None:
                return {
                    "path": file_path,
                    "metadata": json.dumps(metadata),
                    "success": "true",
                    "error": ""
                }
            else:
                return {
                    "path": file_path,
                    "metadata": "{}",
                    "success": "false",
                    "error": "Failed to get file metadata"
                }
        except Exception as e:
            logger.error(f"Error getting metadata for file {file_path}: {e}")
            return {
                "path": file_path,
                "metadata": "{}",
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="set_file_metadata",
        description="Set a single metadata key-value pair for a file"
    )
    async def set_file_metadata(filesystem: str, file_path: str, key: str, value: str) -> Dict[str, str]:
        """Set a single metadata key-value pair for a file."""
        if mcp.client.read_only:
            return {
                "path": file_path,
                "success": "false",
                "error": "Cannot set metadata in read-only mode"
            }

        try:
            success = await mcp.client.set_file_metadata(filesystem, file_path, key, value)
            return {
                "path": file_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to set file metadata"
            }
        except Exception as e:
            logger.error(f"Error setting metadata for file {file_path}: {e}")
            return {
                "path": file_path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="set_file_metadata_json",
        description="Set multiple metadata key-value pairs for a file using JSON"
    )
    async def set_file_metadata_json(filesystem: str, file_path: str, metadata_json: Union[str, Dict[str, str]]) -> Dict[str, str]:
        """Set multiple metadata key-value pairs for a file using JSON."""
        if mcp.client.read_only:
            return {
                "path": file_path,
                "success": "false",
                "error": "Cannot set metadata in read-only mode"
            }

        try:
            if isinstance(metadata_json, dict):
                metadata_json = json.dumps(metadata_json)

            success = await mcp.client.set_file_metadata_json(filesystem, file_path, metadata_json)
            return {
                "path": file_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to set file metadata"
            }
        except Exception as e:
            logger.error(f"Error setting metadata for file {file_path}: {e}")
            return {
                "path": file_path,
                "success": "false",
                "error": str(e)
            }
