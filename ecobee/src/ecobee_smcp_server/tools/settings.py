"""Settings-related MCP tools for Ecobee."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_settings_tools(mcp):
    """Register settings-related MCP tools."""

    @mcp.tool(
        name="get_settings",
        description="Get all thermostat settings"
    )
    async def get_settings(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get thermostat settings.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            settings = await mcp.client.get_settings(thermostat_id)
            if "error" in settings:
                return {"success": "false", "error": settings["error"]}
            return {
                "success": "true",
                "settings": json.dumps(settings)
            }
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_program",
        description="Get the thermostat program including schedule and climate definitions"
    )
    async def get_program(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get thermostat program.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            program = await mcp.client.get_program(thermostat_id)
            if "error" in program:
                return {"success": "false", "error": program["error"]}
            return {
                "success": "true",
                "program": json.dumps(program)
            }
        except Exception as e:
            logger.error(f"Error getting program: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_temperature",
        description="Set temperature hold with heat and cool setpoints"
    )
    async def set_temperature(
        heat_temp: float,
        cool_temp: float,
        thermostat_id: Optional[str] = None,
        hold_type: str = "nextTransition",
        hold_hours: Optional[int] = None
    ) -> Dict[str, str]:
        """Set temperature hold.

        Args:
            heat_temp: Heat setpoint in Fahrenheit
            cool_temp: Cool setpoint in Fahrenheit
            thermostat_id: Optional thermostat ID (uses default if not provided)
            hold_type: Hold type - nextTransition, indefinite, or holdHours
            hold_hours: Number of hours to hold (required if hold_type is holdHours)
        """
        try:
            result = await mcp.client.set_temperature(
                heat_temp, cool_temp, thermostat_id, hold_type, hold_hours
            )
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting temperature: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_mode",
        description="Set HVAC mode: heat, cool, auto, or off"
    )
    async def set_mode(
        mode: str,
        thermostat_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Set HVAC mode.

        Args:
            mode: HVAC mode - heat, cool, auto, or off
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            result = await mcp.client.set_mode(mode, thermostat_id)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting mode: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="resume_program",
        description="Cancel current hold and resume the regular program schedule"
    )
    async def resume_program(
        thermostat_id: Optional[str] = None,
        resume_all: bool = False
    ) -> Dict[str, str]:
        """Resume the regular program.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
            resume_all: If true, resume all events; if false, resume only the most recent
        """
        try:
            result = await mcp.client.resume_program(thermostat_id, resume_all)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error resuming program: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="set_fan_mode",
        description="Set fan mode (auto or on) and optionally fan minimum on time"
    )
    async def set_fan_mode(
        fan_mode: str,
        thermostat_id: Optional[str] = None,
        fan_min_on_time: Optional[int] = None
    ) -> Dict[str, str]:
        """Set fan mode.

        Args:
            fan_mode: Fan mode - auto or on
            thermostat_id: Optional thermostat ID (uses default if not provided)
            fan_min_on_time: Minimum fan on time in minutes per hour (0-55)
        """
        try:
            result = await mcp.client.set_fan_mode(fan_mode, thermostat_id, fan_min_on_time)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error setting fan mode: {e}")
            return {"success": "false", "error": str(e)}
