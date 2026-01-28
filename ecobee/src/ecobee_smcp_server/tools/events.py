"""Events-related MCP tools for Ecobee."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_events_tools(mcp):
    """Register events-related MCP tools."""

    @mcp.tool(
        name="get_events",
        description="Get all active events on the thermostat"
    )
    async def get_events(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get all events.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            events = await mcp.client.get_events(thermostat_id)
            return {
                "success": "true",
                "events": json.dumps(events)
            }
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_vacations",
        description="Get all vacation events"
    )
    async def get_vacations(thermostat_id: Optional[str] = None) -> Dict[str, str]:
        """Get vacation events.

        Args:
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            vacations = await mcp.client.get_vacations(thermostat_id)
            return {
                "success": "true",
                "vacations": json.dumps(vacations)
            }
        except Exception as e:
            logger.error(f"Error getting vacations: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="create_vacation",
        description="Create a vacation event with specified temperature setpoints and duration"
    )
    async def create_vacation(
        name: str,
        cool_temp: float,
        heat_temp: float,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        thermostat_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Create a vacation event.

        Args:
            name: Name for the vacation event
            cool_temp: Cool setpoint in Fahrenheit
            heat_temp: Heat setpoint in Fahrenheit
            start_date: Start date in YYYY-MM-DD format
            start_time: Start time in HH:MM:SS format
            end_date: End date in YYYY-MM-DD format
            end_time: End time in HH:MM:SS format
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            result = await mcp.client.create_vacation(
                name, cool_temp, heat_temp,
                start_date, start_time,
                end_date, end_time,
                thermostat_id
            )
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error creating vacation: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="delete_vacation",
        description="Delete a vacation event by name"
    )
    async def delete_vacation(
        name: str,
        thermostat_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Delete a vacation event.

        Args:
            name: Name of the vacation event to delete
            thermostat_id: Optional thermostat ID (uses default if not provided)
        """
        try:
            result = await mcp.client.delete_vacation(name, thermostat_id)
            return {
                "success": str(result.get("success", False)).lower(),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"Error deleting vacation: {e}")
            return {"success": "false", "error": str(e)}
