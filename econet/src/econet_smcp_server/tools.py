"""MCP tool definitions for EcoNet operations."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all EcoNet tools with the MCP server."""

    # Equipment Discovery

    @mcp.tool()
    def list_equipment() -> Dict[str, str]:
        """List all EcoNet equipment (water heaters and thermostats).

        Returns:
            List of equipment with device_id, name, type, serial_number, and status.
        """
        try:
            equipment = mcp.client.get_equipment()
            return {
                "success": "true",
                "count": str(len(equipment)),
                "equipment": json.dumps(equipment, indent=2)
            }
        except Exception as e:
            logger.error(f"Error listing equipment: {e}")
            return {"success": "false", "error": str(e)}

    # Water Heater Tools

    @mcp.tool()
    def get_water_heater(device_id: Optional[str] = None) -> Dict[str, str]:
        """Get water heater status including mode, temperature, running state.

        Args:
            device_id: Optional device ID. If not provided, uses the first water heater.

        Returns:
            Water heater status including mode, setpoint, running status, hot water level.
        """
        try:
            wh = mcp.client.get_water_heater(device_id)
            return {
                "success": "true",
                "data": json.dumps(wh, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting water heater: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def set_water_heater_mode(mode: str, device_id: Optional[str] = None) -> Dict[str, str]:
        """Set water heater operation mode.

        Args:
            mode: Operation mode (OFF, ENERGY_SAVING, HEAT_PUMP_ONLY, HIGH_DEMAND, ELECTRIC, etc.)
            device_id: Optional device ID. If not provided, uses the first water heater.

        Returns:
            Success status and new mode.
        """
        try:
            mcp.client.set_water_heater_mode(mode, device_id)
            wh = mcp.client.get_water_heater(device_id)

            logger.info(f"Set water heater mode to {mode}")
            return {
                "success": "true",
                "device_id": wh["device_id"],
                "mode": wh["mode"],
            }
        except ValueError as e:
            return {"success": "false", "error": str(e)}
        except Exception as e:
            logger.error(f"Error setting water heater mode: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def set_water_heater_temperature(temperature: int, device_id: Optional[str] = None) -> Dict[str, str]:
        """Set water heater target temperature in Fahrenheit.

        Args:
            temperature: Target temperature in Fahrenheit (typically 90-140)
            device_id: Optional device ID. If not provided, uses the first water heater.

        Returns:
            Success status and new setpoint.
        """
        try:
            mcp.client.set_water_heater_temperature(temperature, device_id)
            wh = mcp.client.get_water_heater(device_id)

            logger.info(f"Set water heater temperature to {temperature}F")
            return {
                "success": "true",
                "device_id": wh["device_id"],
                "setpoint": str(wh["setpoint"]),
            }
        except ValueError as e:
            return {"success": "false", "error": str(e)}
        except Exception as e:
            logger.error(f"Error setting water heater temperature: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_water_heater_energy_usage(device_id: Optional[str] = None) -> Dict[str, str]:
        """Get water heater energy usage report for today.

        Args:
            device_id: Optional device ID. If not provided, uses the first water heater.

        Returns:
            Energy usage data including message and hourly breakdown.
        """
        try:
            usage = mcp.client.get_energy_usage(device_id)
            return {
                "success": "true",
                "device_id": usage["device_id"],
                "message": usage.get("message", ""),
                "data": json.dumps(usage.get("data", []), indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting energy usage: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_water_heater_water_usage(device_id: Optional[str] = None) -> Dict[str, str]:
        """Get water heater water usage report for today.

        Args:
            device_id: Optional device ID. If not provided, uses the first water heater.

        Returns:
            Water usage data with hourly breakdown.
        """
        try:
            usage = mcp.client.get_water_usage(device_id)
            return {
                "success": "true",
                "device_id": usage["device_id"],
                "data": json.dumps(usage.get("data", []), indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting water usage: {e}")
            return {"success": "false", "error": str(e)}

    # Thermostat Tools

    @mcp.tool()
    def get_thermostat(device_id: Optional[str] = None) -> Dict[str, str]:
        """Get thermostat status including mode, temperature, humidity.

        Args:
            device_id: Optional device ID. If not provided, uses the first thermostat.

        Returns:
            Thermostat status including mode, setpoints, humidity, fan settings.
        """
        try:
            th = mcp.client.get_thermostat(device_id)
            return {
                "success": "true",
                "data": json.dumps(th, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting thermostat: {e}")
            return {"success": "false", "error": str(e)}

    logger.info("Registered EcoNet MCP tools: list_equipment, get_water_heater, "
                "set_water_heater_mode, set_water_heater_temperature, "
                "get_water_heater_energy_usage, get_water_heater_water_usage, get_thermostat")
