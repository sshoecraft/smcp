# InfluxDB SMCP Server

An MCP server for InfluxDB 1.8+ with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides query and write access to InfluxDB time-series databases via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives InfluxDB credentials via SMCP handshake (no CLI args, no env vars, no disk)
- **Query Support**: Execute any InfluxQL query
- **Write Support**: Write data points with tags and fields
- **Database Discovery**: List databases, measurements, and retention policies
- **SSL/TLS Support**: Optional encrypted connections

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `INFLUXDB_HOST` | Yes | InfluxDB hostname/IP |
| `INFLUXDB_PORT` | No | Port (default: 8086) |
| `INFLUXDB_USERNAME` | No | Username for authentication |
| `INFLUXDB_PASSWORD` | No | Password for authentication |
| `INFLUXDB_SSL` | No | Use SSL (`true`/`false`, default: false) |
| `INFLUXDB_VERIFY_SSL` | No | Verify SSL certificates (default: true) |
| `INFLUXDB_DATABASE` | No | Default database |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add influxdb --command "influxdb-smcp-server" --credential "INFLUXDB_HOST=localhost" --credential "INFLUXDB_PORT=8086" --credential "INFLUXDB_USERNAME=admin" --credential "INFLUXDB_PASSWORD=..." --credential "INFLUXDB_DATABASE=telegraf"
```

## Usage

```bash
influxdb-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"INFLUXDB_HOST":"localhost","INFLUXDB_USERNAME":"admin","INFLUXDB_PASSWORD":"secret"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### list_databases

List all InfluxDB databases.

**Parameters:** None

**Returns:** `{success, count, databases}` where databases is a JSON array of names

### list_measurements

List all measurements in a database.

**Parameters:**
- `database` (string, required): Database name

**Returns:** `{success, database, count, measurements}`

### list_retention_policies

List retention policies for a database.

**Parameters:**
- `database` (string, required): Database name

**Returns:** `{success, database, count, policies}`

### query

Execute an InfluxQL query.

**Parameters:**
- `database` (string, required): Database to query
- `query` (string, required): InfluxQL query string

**Returns:** `{success, database, row_count, results}` where results is a JSON array of row objects

**Examples:**
```
SELECT * FROM cpu WHERE host='server01' LIMIT 10
SELECT mean(value) FROM temperature WHERE time > now() - 1h GROUP BY time(5m)
SHOW TAG KEYS FROM cpu
SHOW FIELD KEYS FROM cpu
```

### write

Write a data point to InfluxDB.

**Parameters:**
- `database` (string, required): Database to write to
- `measurement` (string, required): Measurement name
- `fields` (string, required): JSON object of field values (e.g., `{"value": 42.5}`)
- `tags` (string, optional): JSON object of tag values (e.g., `{"host": "server1"}`)
- `time` (string, optional): Timestamp in ISO8601 format or epoch nanoseconds

**Returns:** `{success, database, measurement}`

**Example:**
```json
{
  "database": "mydb",
  "measurement": "temperature",
  "fields": "{\"value\": 23.5}",
  "tags": "{\"location\": \"office\", \"sensor\": \"temp1\"}"
}
```

## Building

```bash
pip install -e ../lib  # Install shared smcp library
pip install -e .
```

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

child = subprocess.Popen(
    ["influxdb-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "INFLUXDB_HOST": "localhost",
    "INFLUXDB_PORT": "8086",
    "INFLUXDB_USERNAME": "admin",
    "INFLUXDB_PASSWORD": "secret"
}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## InfluxQL Quick Reference

```sql
-- Show databases
SHOW DATABASES

-- Show measurements
SHOW MEASUREMENTS

-- Show tag keys
SHOW TAG KEYS FROM "cpu"

-- Show field keys
SHOW FIELD KEYS FROM "cpu"

-- Select data
SELECT * FROM "cpu" WHERE time > now() - 1h LIMIT 10

-- Aggregation
SELECT mean("value") FROM "temperature" WHERE time > now() - 24h GROUP BY time(1h)

-- Group by tags
SELECT mean("value") FROM "temperature" GROUP BY "location"
```

## Security

- Credentials exist only in process memory
- No environment variables exposed in `/proc/<pid>/environ`
- No CLI arguments visible in `ps aux`
- No credentials written to disk
- Parent process controls credential distribution

## License

MIT
