"""Climate/thermostat-related MCP tools for HomeKit."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_climate_tools(mcp):
    """Register climate-related MCP tools."""

    @mcp.tool(
        name="get_thermostat",
        description="Get thermostat state. Returns current_temp, target_temp (for heat/cool mode), heat_to and cool_to (for auto mode), mode, and humidity. All temperatures in Celsius."
    )
    async def get_thermostat(aid: int = 1) -> Dict[str, str]:
        """Get thermostat state.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            state = await mcp.client.get_thermostat_state(aid)
            if "error" in state:
                return {"success": "false", "error": state["error"]}
            return {
                "success": "true",
                "current_temp": str(state.get("current_temperature", "")),
                "target_temp": str(state.get("target_temperature", "")),
                "mode": str(state.get("target_state", "")),
                "status": str(state.get("current_state", "")),
                "heat_to": str(state.get("heating_threshold", "")),
                "cool_to": str(state.get("cooling_threshold", "")),
                "humidity": str(state.get("humidity", ""))
            }
        except Exception as e:
            logger.error(f"Error getting thermostat state: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_thermostat",
        description="Set thermostat temperature. In heat or cool mode, use target_temperature. In auto mode, use heat_to (heating starts below this) and cool_to (cooling starts above this). All temperatures in Celsius. mode can be: off, heat, cool, auto."
    )
    async def set_thermostat(
        aid: int = 1,
        target_temperature: Optional[float] = None,
        mode: Optional[str] = None,
        heat_to: Optional[float] = None,
        cool_to: Optional[float] = None
    ) -> Dict[str, str]:
        """Set thermostat state.

        Args:
            aid: Numeric accessory ID (default: 1)
            target_temperature: Target temp in Celsius (use in heat or cool mode)
            mode: Target mode - off, heat, cool, or auto
            heat_to: Heat-to temp in Celsius (use in auto mode - heating starts below this)
            cool_to: Cool-to temp in Celsius (use in auto mode - cooling starts above this)
        """
        try:
            result = await mcp.client.set_thermostat_state(
                aid=aid,
                target_temperature=target_temperature,
                target_state=mode,
                heating_threshold=heat_to,
                cooling_threshold=cool_to
            )
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting thermostat state: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_thermostat_mode",
        description="Set thermostat mode: off, heat, cool, or auto. aid is numeric (usually 1)."
    )
    async def set_thermostat_mode(mode: str, aid: int = 1) -> Dict[str, str]:
        """Set thermostat mode.

        Args:
            mode: Target mode - off, heat, cool, or auto
            aid: Numeric accessory ID (default: 1)
        """
        valid_modes = ["off", "heat", "cool", "auto"]
        if mode not in valid_modes:
            return {"success": "false", "error": f"Invalid mode. Must be one of: {valid_modes}"}

        try:
            result = await mcp.client.set_thermostat_state(aid=aid, target_state=mode)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting thermostat mode: {e}")
            return {"success": "false", "error": str(e)}
