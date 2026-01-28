"""Generic MCP tools for HomeKit devices."""

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def register_generic_tools(mcp):
    """Register generic HomeKit MCP tools."""

    @mcp.tool(
        name="list_accessories",
        description="List all HomeKit accessories with their numeric aid (accessory ID), services, and characteristics. Use this first to find the aid values for other commands."
    )
    async def list_accessories() -> Dict[str, str]:
        """List all accessories."""
        try:
            accessories = await mcp.client.list_accessories()
            return {
                "success": "true",
                "accessories": json.dumps(accessories, indent=2)
            }
        except Exception as e:
            logger.error(f"Error listing accessories: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_accessory_info",
        description="Get information about a specific accessory (name, manufacturer, model, etc.). aid is numeric (usually 1) - use list_accessories to find."
    )
    async def get_accessory_info(aid: int = 1) -> Dict[str, str]:
        """Get accessory information.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            info = await mcp.client.get_accessory_info(aid)
            return {
                "success": "true",
                "info": json.dumps(info)
            }
        except Exception as e:
            logger.error(f"Error getting accessory info: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_characteristics",
        description="Get values of specific characteristics. Parameter must be a JSON array of [aid, iid] pairs. Example: '[[1, 10], [1, 11]]' to get characteristics 10 and 11 from accessory 1."
    )
    async def get_characteristics(characteristics: str) -> Dict[str, str]:
        """Get characteristic values.

        Args:
            characteristics: JSON array of [aid, iid] pairs, e.g. '[[1, 10], [1, 11]]'
        """
        try:
            char_list = json.loads(characteristics)
            # Convert to list of tuples
            char_tuples = [(c[0], c[1]) for c in char_list]
            result = await mcp.client.get_characteristics(char_tuples)
            return {
                "success": "true",
                "values": json.dumps(result)
            }
        except json.JSONDecodeError as e:
            return {"success": "false", "error": f"Invalid JSON: {e}"}
        except Exception as e:
            logger.error(f"Error getting characteristics: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_characteristics",
        description="Set characteristic values (requires write permission). Parameter must be a JSON object mapping 'aid.iid' strings to values. Example: '{\"1.10\": true, \"1.11\": 50}' to set characteristic 10 to true and 11 to 50 on accessory 1."
    )
    async def set_characteristics(characteristics: str) -> Dict[str, str]:
        """Set characteristic values.

        Args:
            characteristics: JSON object mapping 'aid.iid' to values, e.g. '{"1.10": true, "1.11": 50}'
        """
        try:
            char_dict = json.loads(characteristics)
            # Convert to dict with tuple keys
            char_tuples = {}
            for key, value in char_dict.items():
                parts = key.split(".")
                aid = int(parts[0])
                iid = int(parts[1])
                char_tuples[(aid, iid)] = value

            result = await mcp.client.set_characteristics(char_tuples)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except json.JSONDecodeError as e:
            return {"success": "false", "error": f"Invalid JSON: {e}"}
        except Exception as e:
            logger.error(f"Error setting characteristics: {e}")
            return {"success": "false", "error": str(e)}
