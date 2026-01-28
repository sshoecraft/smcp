"""Light-related MCP tools for HomeKit."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_light_tools(mcp):
    """Register light-related MCP tools."""

    @mcp.tool(
        name="get_light",
        description="Get the current state of a light (on/off, brightness, color). aid is numeric (usually 1) - use list_accessories to find devices."
    )
    async def get_light(aid: int = 1) -> Dict[str, str]:
        """Get light state.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            state = await mcp.client.get_light_state(aid)
            if "error" in state:
                return {"success": "false", "error": state["error"]}
            return {
                "success": "true",
                "on": str(state.get("on", False)).lower(),
                "brightness": str(state.get("brightness", "")),
                "hue": str(state.get("hue", "")),
                "saturation": str(state.get("saturation", ""))
            }
        except Exception as e:
            logger.error(f"Error getting light state: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_light",
        description="Control a light - turn on/off, set brightness (0-100), or set color (hue 0-360, saturation 0-100). aid is numeric (usually 1)."
    )
    async def set_light(
        aid: int = 1,
        on: Optional[bool] = None,
        brightness: Optional[int] = None,
        hue: Optional[float] = None,
        saturation: Optional[float] = None
    ) -> Dict[str, str]:
        """Set light state.

        Args:
            aid: Numeric accessory ID (default: 1)
            on: Turn light on (true) or off (false)
            brightness: Brightness level 0-100
            hue: Color hue 0-360
            saturation: Color saturation 0-100
        """
        try:
            result = await mcp.client.set_light_state(
                aid=aid,
                on=on,
                brightness=brightness,
                hue=hue,
                saturation=saturation
            )
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting light state: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="turn_on_light",
        description="Turn on a light. aid is numeric (usually 1)."
    )
    async def turn_on_light(aid: int = 1) -> Dict[str, str]:
        """Turn on a light.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            result = await mcp.client.set_light_state(aid=aid, on=True)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error turning on light: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="turn_off_light",
        description="Turn off a light. aid is numeric (usually 1)."
    )
    async def turn_off_light(aid: int = 1) -> Dict[str, str]:
        """Turn off a light.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            result = await mcp.client.set_light_state(aid=aid, on=False)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error turning off light: {e}")
            return {"success": "false", "error": str(e)}
