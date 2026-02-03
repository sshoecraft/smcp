"""PostgreSQL client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


@dataclass
class PostgresConfig:
    """Configuration for PostgreSQL client."""
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    database: str = "postgres"

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "PostgresConfig":
        """Create config from SMCP credentials."""
        # If DATABASE_URL is provided, parse it
        if "DATABASE_URL" in creds:
            return cls.from_url(creds["DATABASE_URL"])

        return cls(
            host=creds.get("DB_HOST", "localhost"),
            port=int(creds.get("DB_PORT", "5432")),
            user=creds.get("DB_USER", "postgres"),
            password=creds.get("DB_PASS", ""),
            database=creds.get("DB_NAME", "postgres"),
        )

    @classmethod
    def from_url(cls, url: str) -> "PostgresConfig":
        """Parse a PostgreSQL connection URL."""
        # Handle postgresql:// or postgres:// URLs
        from urllib.parse import urlparse
        parsed = urlparse(url)

        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            user=parsed.username or "postgres",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") or "postgres",
        )

    def to_conninfo(self) -> str:
        """Build a connection string."""
        password = quote_plus(self.password) if self.password else ""
        if password:
            return f"postgresql://{self.user}:{password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"


class PostgresClient:
    """PostgreSQL client wrapper."""

    def __init__(self, config: PostgresConfig):
        """Initialize the PostgreSQL client.

        Args:
            config: PostgresConfig instance with credentials
        """
        self._config = config
        self._conninfo = config.to_conninfo()

    @property
    def config(self) -> PostgresConfig:
        """The configuration for the client."""
        return self._config

    def _get_connection(self) -> psycopg.Connection:
        """Get a new database connection."""
        return psycopg.connect(self._conninfo, row_factory=dict_row)

    async def list_tables(self, schema: str = "public") -> List[str]:
        """List all tables in the specified schema.

        Args:
            schema: The schema to list tables from (default: public)
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = %s",
                        (schema,)
                    )
                    return [row["table_name"] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    async def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get schema information for a table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT column_name, data_type "
                        "FROM information_schema.columns "
                        "WHERE table_name = %s",
                        (table_name,)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return []

    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute a read-only SQL query.

        Args:
            sql: The SQL query to execute

        Returns:
            Dict with 'rows' containing query results or 'error' on failure
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Start read-only transaction
                    cur.execute("BEGIN TRANSACTION READ ONLY")
                    try:
                        cur.execute(sql)
                        rows = [dict(row) for row in cur.fetchall()]
                        return {"rows": rows, "row_count": len(rows)}
                    finally:
                        cur.execute("ROLLBACK")
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}
