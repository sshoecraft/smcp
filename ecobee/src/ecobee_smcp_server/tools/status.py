"""Status-related MCP tools for Ecobee."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_status_tools(mcp):
    """Register status-related MCP tools."""

    @mcp.tool(
        name="list_thermostats",
        description="List all thermostats registered to the account"
    )
    async def list_thermostats() -> Dict[str, str]:
        """List all thermostats."""
        try:
            thermostats = await mcp.client.list_thermostats()
            return {
                "success": "true",
                "thermostats": json.dumps(thermostats)
            }
        except Exception as e:
            logger.error(f"Error listing thermostats: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_thermostat_info",
        description="Get basic thermostat info including name, time, and location"
    )
    async def get_thermostat_info(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get thermostat info.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            info = await mcp.client.get_thermostat_info(thermostat_id)
            if "error" in info:
                return {"success": "false", "error": info["error"]}
            return {
                "success": "true",
                "info": json.dumps(info)
            }
        except Exception as e:
            logger.error(f"Error getting thermostat info: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_temperature",
        description="Get current temperature, humidity, and setpoints"
    )
    async def get_temperature(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get current temperature reading.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            temp_data = await mcp.client.get_temperature(thermostat_id)
            if "error" in temp_data:
                return {"success": "false", "error": temp_data["error"]}
            return {
                "success": "true",
                "temperature": str(temp_data.get("temperature", "")),
                "humidity": str(temp_data.get("humidity", "")),
                "desired_heat": str(temp_data.get("desired_heat", "")),
                "desired_cool": str(temp_data.get("desired_cool", "")),
                "last_modified": str(temp_data.get("last_modified", ""))
            }
        except Exception as e:
            logger.error(f"Error getting temperature: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_sensors",
        description="Get all remote sensor readings including temperature, humidity, and occupancy"
    )
    async def get_sensors(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get all sensor readings.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            sensors = await mcp.client.get_sensors(thermostat_id)
            return {
                "success": "true",
                "sensors": json.dumps(sensors)
            }
        except Exception as e:
            logger.error(f"Error getting sensors: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_runtime",
        description="Get runtime data including HVAC activity and temperature history"
    )
    async def get_runtime(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get runtime data.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            runtime = await mcp.client.get_runtime(thermostat_id)
            if "error" in runtime:
                return {"success": "false", "error": runtime["error"]}
            return {
                "success": "true",
                "runtime": json.dumps(runtime)
            }
        except Exception as e:
            logger.error(f"Error getting runtime: {e}")
            return {"success": "false", "error": str(e)}
