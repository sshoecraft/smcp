"""Blob MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_blob_tools(mcp):
    """Register blob related MCP tools."""

    @mcp.tool(
        name="list_blobs",
        description="List blobs in a container, optionally filtered by prefix"
    )
    async def list_blobs(container: str, prefix: str = "") -> Dict[str, str]:
        """List blobs in a container."""
        try:
            blobs = await mcp.client.list_blobs(container, prefix)
            return {
                "success": "true",
                "container": container,
                "blobs": json.dumps(blobs),
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error listing blobs in {container}: {e}")
            return {
                "success": "false",
                "container": container,
                "blobs": "[]",
                "error": str(e)
            }

    @mcp.tool(
        name="get_blob_properties",
        description="Get properties of a blob in the specified container"
    )
    async def get_blob_properties(container: str, blob_path: str) -> Dict[str, str]:
        """Get properties of a blob."""
        try:
            properties = await mcp.client.get_blob_properties(container, blob_path)
            if properties is not None:
                return {
                    "path": blob_path,
                    "properties": json.dumps(properties),
                    "success": "true",
                    "error": ""
                }
            else:
                return {
                    "path": blob_path,
                    "properties": "{}",
                    "success": "false",
                    "error": "Failed to get blob properties"
                }
        except Exception as e:
            logger.error(f"Error getting properties for blob {blob_path}: {e}")
            return {
                "path": blob_path,
                "properties": "{}",
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="upload_blob",
        description="Upload a file as a blob to the specified container"
    )
    async def upload_blob(upload_file: str, container: str, destination: str) -> Dict[str, str]:
        """Upload a file as a blob."""
        if mcp.client.read_only:
            return {
                "source": upload_file,
                "destination": destination,
                "success": "false",
                "error": "Cannot upload blob in read-only mode"
            }

        try:
            success = await mcp.client.upload_blob(upload_file, container, destination)
            return {
                "source": upload_file,
                "destination": destination,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to upload blob"
            }
        except Exception as e:
            logger.error(f"Error uploading blob {upload_file} to {destination}: {e}")
            return {
                "source": upload_file,
                "destination": destination,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="upload_blob_content",
        description="Upload text or base64-encoded content directly as a blob (no local file needed). Use encoding='utf-8' for text, 'base64' for binary data like PDFs."
    )
    async def upload_blob_content(
        content: str,
        container: str,
        destination: str,
        encoding: str = "utf-8"
    ) -> Dict[str, str]:
        """Upload content directly as a blob."""
        if mcp.client.read_only:
            return {
                "destination": destination,
                "success": "false",
                "error": "Cannot upload blob in read-only mode"
            }

        try:
            await mcp.client.upload_blob_content(content, container, destination, encoding)
            return {
                "destination": destination,
                "container": container,
                "success": "true",
                "error": ""
            }
        except Exception as e:
            logger.error(f"Error uploading content to {container}/{destination}: {e}")
            return {
                "destination": destination,
                "container": container,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="download_blob",
        description="Download a blob from the specified container"
    )
    async def download_blob(container: str, source: str, download_path: str) -> Dict[str, str]:
        """Download a blob from a container."""
        try:
            success = await mcp.client.download_blob(container, source, download_path)
            return {
                "source": source,
                "destination": download_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to download blob"
            }
        except Exception as e:
            logger.error(f"Error downloading blob {source} to {download_path}: {e}")
            return {
                "source": source,
                "destination": download_path,
                "success": "false",
                "error": str(e)
            }

    @mcp.tool(
        name="delete_blob",
        description="Delete a blob from the specified container"
    )
    async def delete_blob(container: str, blob_path: str) -> Dict[str, str]:
        """Delete a blob from a container."""
        if mcp.client.read_only:
            return {
                "path": blob_path,
                "success": "false",
                "error": "Cannot delete blob in read-only mode"
            }

        try:
            success = await mcp.client.delete_blob(container, blob_path)
            return {
                "path": blob_path,
                "success": "true" if success else "false",
                "error": "" if success else "Failed to delete blob"
            }
        except Exception as e:
            logger.error(f"Error deleting blob {blob_path}: {e}")
            return {
                "path": blob_path,
                "success": "false",
                "error": str(e)
            }
