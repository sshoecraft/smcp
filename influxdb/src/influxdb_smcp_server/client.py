"""InfluxDB client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from influxdb import InfluxDBClient as InfluxClient

logger = logging.getLogger(__name__)


@dataclass
class InfluxDBConfig:
    """Configuration for InfluxDB client."""
    host: str
    port: int = 8086
    username: str = ""
    password: str = ""
    ssl: bool = False
    verify_ssl: bool = True
    database: str = ""

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "InfluxDBConfig":
        """Create config from SMCP credentials."""
        host = creds.get("INFLUXDB_HOST")
        if not host:
            raise ValueError("INFLUXDB_HOST credential is required")

        return cls(
            host=host,
            port=int(creds.get("INFLUXDB_PORT", "8086")),
            username=creds.get("INFLUXDB_USERNAME", ""),
            password=creds.get("INFLUXDB_PASSWORD", ""),
            ssl=creds.get("INFLUXDB_SSL", "").lower() == "true",
            verify_ssl=creds.get("INFLUXDB_VERIFY_SSL", "true").lower() != "false",
            database=creds.get("INFLUXDB_DATABASE", ""),
        )


class InfluxDBClient:
    """InfluxDB client wrapper for MCP tools."""

    def __init__(self, config: InfluxDBConfig):
        """Initialize the InfluxDB client.

        Args:
            config: InfluxDBConfig instance with connection settings
        """
        self.config = config
        self.client: Optional[InfluxClient] = None

    def connect(self):
        """Connect to InfluxDB."""
        logger.info(f"Connecting to InfluxDB at {self.config.host}:{self.config.port}")

        self.client = InfluxClient(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username or None,
            password=self.config.password or None,
            ssl=self.config.ssl,
            verify_ssl=self.config.verify_ssl,
            database=self.config.database or None,
        )

        # Test connection
        try:
            self.client.ping()
            logger.info("Connected to InfluxDB successfully")
        except Exception as e:
            logger.warning(f"Could not ping InfluxDB: {e}. Will retry on first query.")

    def list_databases(self) -> List[str]:
        """List all databases.

        Returns:
            List of database names
        """
        try:
            result = self.client.get_list_database()
            return [db["name"] for db in result]
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            raise

    def list_measurements(self, database: str) -> List[str]:
        """List measurements in a database.

        Args:
            database: Database name

        Returns:
            List of measurement names
        """
        try:
            self.client.switch_database(database)
            result = self.client.query("SHOW MEASUREMENTS")
            measurements = []
            for point in result.get_points():
                measurements.append(point.get("name", ""))
            return measurements
        except Exception as e:
            logger.error(f"Error listing measurements in {database}: {e}")
            raise

    def list_retention_policies(self, database: str) -> List[Dict[str, Any]]:
        """List retention policies for a database.

        Args:
            database: Database name

        Returns:
            List of retention policy dicts
        """
        try:
            result = self.client.get_list_retention_policies(database)
            return result
        except Exception as e:
            logger.error(f"Error listing retention policies for {database}: {e}")
            raise

    def query(self, database: str, query_str: str) -> List[Dict[str, Any]]:
        """Execute an InfluxQL query.

        Args:
            database: Database to query
            query_str: InfluxQL query string

        Returns:
            List of result rows as dicts
        """
        try:
            self.client.switch_database(database)
            result = self.client.query(query_str)

            rows = []
            for measurement, points in result.items():
                measurement_name = measurement[0] if isinstance(measurement, tuple) else measurement
                for point in points:
                    row = {"_measurement": measurement_name}
                    row.update(point)
                    rows.append(row)

            return rows
        except Exception as e:
            logger.error(f"Error executing query on {database}: {e}")
            raise

    def write(
        self,
        database: str,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        time: Optional[str] = None
    ) -> bool:
        """Write a data point to InfluxDB.

        Args:
            database: Database to write to
            measurement: Measurement name
            tags: Tag key-value pairs
            fields: Field key-value pairs
            time: Optional timestamp (ISO8601 or epoch nanoseconds)

        Returns:
            True if successful
        """
        try:
            self.client.switch_database(database)

            point = {
                "measurement": measurement,
                "tags": tags,
                "fields": fields,
            }

            if time:
                point["time"] = time

            self.client.write_points([point])
            logger.info(f"Wrote point to {database}.{measurement}")
            return True
        except Exception as e:
            logger.error(f"Error writing to {database}.{measurement}: {e}")
            raise
