"""Sensor-related MCP tools for HomeKit."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_sensor_tools(mcp):
    """Register sensor-related MCP tools."""

    @mcp.tool(
        name="get_sensors",
        description="Get all sensor values from an accessory (temperature, humidity, motion, contact, etc.). The aid parameter is a numeric ID (usually 1 for the main device) - use list_accessories to see available aids."
    )
    async def get_sensors(aid: int = 1) -> Dict[str, str]:
        """Get sensor values.

        Args:
            aid: Numeric accessory ID (default: 1, use list_accessories to find)
        """
        try:
            sensors = await mcp.client.get_sensor_values(aid)
            if "error" in sensors:
                return {"success": "false", "error": sensors["error"]}
            return {
                "success": "true",
                "sensors": json.dumps(sensors)
            }
        except Exception as e:
            logger.error(f"Error getting sensor values: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_temperature_sensor",
        description="Get temperature reading from a sensor accessory. aid is numeric (usually 1) - use list_accessories if unsure."
    )
    async def get_temperature_sensor(aid: int = 1) -> Dict[str, str]:
        """Get temperature sensor reading.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            sensors = await mcp.client.get_sensor_values(aid)
            if "error" in sensors:
                return {"success": "false", "error": sensors["error"]}
            if "temperature" in sensors:
                return {
                    "success": "true",
                    "temperature": str(sensors["temperature"])
                }
            return {"success": "false", "error": "No temperature sensor found"}
        except Exception as e:
            logger.error(f"Error getting temperature: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_humidity_sensor",
        description="Get humidity reading from a sensor accessory. aid is numeric (usually 1)."
    )
    async def get_humidity_sensor(aid: int = 1) -> Dict[str, str]:
        """Get humidity sensor reading.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            sensors = await mcp.client.get_sensor_values(aid)
            if "error" in sensors:
                return {"success": "false", "error": sensors["error"]}
            if "humidity" in sensors:
                return {
                    "success": "true",
                    "humidity": str(sensors["humidity"])
                }
            return {"success": "false", "error": "No humidity sensor found"}
        except Exception as e:
            logger.error(f"Error getting humidity: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_motion_sensor",
        description="Check if motion is detected. aid is numeric (usually 1)."
    )
    async def get_motion_sensor(aid: int = 1) -> Dict[str, str]:
        """Get motion sensor state.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            sensors = await mcp.client.get_sensor_values(aid)
            if "error" in sensors:
                return {"success": "false", "error": sensors["error"]}
            if "motion" in sensors:
                return {
                    "success": "true",
                    "motion_detected": str(sensors["motion"]).lower()
                }
            return {"success": "false", "error": "No motion sensor found"}
        except Exception as e:
            logger.error(f"Error getting motion sensor: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_contact_sensor",
        description="Check contact sensor state (open/closed for doors, windows). aid is numeric (usually 1)."
    )
    async def get_contact_sensor(aid: int = 1) -> Dict[str, str]:
        """Get contact sensor state.

        Args:
            aid: Numeric accessory ID (default: 1)
        """
        try:
            sensors = await mcp.client.get_sensor_values(aid)
            if "error" in sensors:
                return {"success": "false", "error": sensors["error"]}
            if "contact" in sensors:
                return {
                    "success": "true",
                    "state": sensors["contact"]
                }
            return {"success": "false", "error": "No contact sensor found"}
        except Exception as e:
            logger.error(f"Error getting contact sensor: {e}")
            return {"success": "false", "error": str(e)}
