"""PostgreSQL MCP Server with SMCP credential injection."""

import json
import logging
import sys
from typing import Dict

from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake

from postgres_smcp_server.client import PostgresClient, PostgresConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)


def create_server(client: PostgresClient) -> FastMCP:
    """Create and configure the MCP server with tools."""
    mcp = FastMCP("PostgresSMCP")

    @mcp.tool(
        name="query",
        description="Run a read-only SQL query"
    )
    async def query(sql: str) -> Dict[str, str]:
        """Execute a read-only SQL query.

        Args:
            sql: The SQL query to execute

        Returns:
            Dict containing query results or error
        """
        result = await client.execute_query(sql)
        if "error" in result:
            return {"success": "false", "error": result["error"]}
        return {
            "success": "true",
            "rows": json.dumps(result["rows"], default=str),
            "row_count": str(result["row_count"])
        }

    @mcp.tool(
        name="list_tables",
        description="List all tables in a schema"
    )
    async def list_tables(schema: str = "public") -> Dict[str, str]:
        """List all tables in the specified schema.

        Args:
            schema: The schema to list tables from (default: public)
        """
        tables = await client.list_tables(schema)
        return {"success": "true", "tables": json.dumps(tables)}

    @mcp.tool(
        name="get_table_schema",
        description="Get column information for a table"
    )
    async def get_table_schema(table_name: str) -> Dict[str, str]:
        """Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dict containing column names and types
        """
        schema = await client.get_table_schema(table_name)
        if not schema:
            return {"success": "false", "error": f"Table '{table_name}' not found or has no columns"}
        return {"success": "true", "columns": json.dumps(schema)}

    return mcp


def main():
    """Main entry point for the PostgreSQL SMCP service."""
    try:
        # Perform SMCP handshake to get credentials
        creds = smcp_handshake()

        # Configure logging level from credentials if provided
        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Create PostgreSQL client from credentials
        config = PostgresConfig.from_smcp_creds(creds)
        client = PostgresClient(config)

        # Create and run MCP server
        mcp = create_server(client)

        logger.info("Starting PostgreSQL SMCP service")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Error starting PostgreSQL SMCP service: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
