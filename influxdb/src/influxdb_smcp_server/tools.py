"""MCP tool definitions for InfluxDB operations."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all InfluxDB tools with the MCP server."""

    @mcp.tool(
        name="list_databases",
        description="List all InfluxDB databases"
    )
    async def list_databases() -> Dict[str, str]:
        """List all available InfluxDB databases.

        Returns:
            Dict with list of database names
        """
        try:
            databases = mcp.client.list_databases()
            return {
                "success": "true",
                "count": str(len(databases)),
                "databases": json.dumps(databases)
            }
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="list_measurements",
        description="List all measurements in an InfluxDB database"
    )
    async def list_measurements(database: str) -> Dict[str, str]:
        """List all measurements in a database.

        Args:
            database: The database name

        Returns:
            Dict with list of measurement names
        """
        try:
            measurements = mcp.client.list_measurements(database)
            return {
                "success": "true",
                "database": database,
                "count": str(len(measurements)),
                "measurements": json.dumps(measurements)
            }
        except Exception as e:
            logger.error(f"Error listing measurements: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="list_retention_policies",
        description="List retention policies for an InfluxDB database"
    )
    async def list_retention_policies(database: str) -> Dict[str, str]:
        """List retention policies for a database.

        Args:
            database: The database name

        Returns:
            Dict with list of retention policies
        """
        try:
            policies = mcp.client.list_retention_policies(database)
            return {
                "success": "true",
                "database": database,
                "count": str(len(policies)),
                "policies": json.dumps(policies)
            }
        except Exception as e:
            logger.error(f"Error listing retention policies: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="query",
        description="Execute an InfluxQL query against an InfluxDB database"
    )
    async def query(database: str, query: str) -> Dict[str, str]:
        """Execute an InfluxQL query.

        Args:
            database: The database to query
            query: The InfluxQL query string (e.g., "SELECT * FROM cpu LIMIT 10")

        Returns:
            Dict with query results as JSON array
        """
        try:
            rows = mcp.client.query(database, query)
            return {
                "success": "true",
                "database": database,
                "row_count": str(len(rows)),
                "results": json.dumps(rows, default=str)
            }
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="write",
        description="Write a data point to an InfluxDB database"
    )
    async def write(
        database: str,
        measurement: str,
        fields: str,
        tags: Optional[str] = None,
        time: Optional[str] = None
    ) -> Dict[str, str]:
        """Write a data point to InfluxDB.

        Args:
            database: The database to write to
            measurement: The measurement name
            fields: JSON object of field key-value pairs (e.g., '{"value": 42.5, "status": "ok"}')
            tags: Optional JSON object of tag key-value pairs (e.g., '{"host": "server1"}')
            time: Optional timestamp (ISO8601 format or epoch nanoseconds)

        Returns:
            Dict with success status
        """
        try:
            # Parse fields JSON
            try:
                fields_dict = json.loads(fields)
            except json.JSONDecodeError as e:
                return {"success": "false", "error": f"Invalid fields JSON: {e}"}

            # Parse tags JSON if provided
            tags_dict = {}
            if tags:
                try:
                    tags_dict = json.loads(tags)
                except json.JSONDecodeError as e:
                    return {"success": "false", "error": f"Invalid tags JSON: {e}"}

            mcp.client.write(
                database=database,
                measurement=measurement,
                tags=tags_dict,
                fields=fields_dict,
                time=time
            )

            return {
                "success": "true",
                "database": database,
                "measurement": measurement
            }
        except Exception as e:
            logger.error(f"Error writing data point: {e}")
            return {"success": "false", "error": str(e)}
