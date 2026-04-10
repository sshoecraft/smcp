"""SAS URL generation MCP tools."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_sas_tools(mcp):
    """Register SAS URL related MCP tools."""

    @mcp.tool(
        name="generate_sas_url",
        description="Generate a time-limited SAS URL for a blob, allowing direct download without Azure credentials"
    )
    async def generate_sas_url(
        container: str,
        blob_path: str,
        expiry_minutes: int = 60,
        permissions: str = "r"
    ) -> Dict[str, str]:
        """Generate a SAS URL for a blob."""
        try:
            url = await mcp.client.generate_sas_url(container, blob_path, expiry_minutes, permissions)
            if url:
                return {
                    "success": "true",
                    "container": container,
                    "blob_path": blob_path,
                    "sas_url": url,
                    "expiry_minutes": str(expiry_minutes),
                    "permissions": permissions,
                    "error": ""
                }
            else:
                return {
                    "success": "false",
                    "container": container,
                    "blob_path": blob_path,
                    "sas_url": "",
                    "expiry_minutes": str(expiry_minutes),
                    "permissions": permissions,
                    "error": "Failed to generate SAS URL (storage account key may be missing)"
                }
        except Exception as e:
            logger.error(f"Error generating SAS URL for {container}/{blob_path}: {e}")
            return {
                "success": "false",
                "container": container,
                "blob_path": blob_path,
                "sas_url": "",
                "expiry_minutes": str(expiry_minutes),
                "permissions": permissions,
                "error": str(e)
            }
