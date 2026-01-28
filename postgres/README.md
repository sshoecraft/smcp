# PostgreSQL SMCP Server

An MCP server for PostgreSQL with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides read-only access to PostgreSQL databases via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives database credentials via SMCP handshake (no CLI args, no env vars, no disk)
- **Read-Only Access**: All queries execute within READ ONLY transactions
- **Schema Discovery**: List tables and get column information

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Description |
|------------|-------------|
| `DATABASE_URL` | Full PostgreSQL connection string (takes precedence) |
| `DB_HOST` | Database host (default: localhost) |
| `DB_PORT` | Database port (default: 5432) |
| `DB_USER` | Database user (default: postgres) |
| `DB_PASS` | Database password |
| `DB_NAME` | Database name (default: postgres) |
| `LOG_LEVEL` | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add postgres --command "postgres-smcp-server" --credential "DATABASE_URL=postgresql://user:pass@host:5432/dbname"
```

Or with individual credentials:

```bash
shepherd smcp add postgres --command "postgres-smcp-server" --credential "DB_HOST=localhost" --credential "DB_PORT=5432" --credential "DB_USER=postgres" --credential "DB_PASS=..." --credential "DB_NAME=mydb"
```

## Usage

```bash
postgres-smcp-server
```

The server performs the SMCP handshake on startup:

```
← +READY
→ {"DB_HOST":"postgres.local","DB_USER":"app","DB_PASS":"secret","DB_NAME":"mydb"}
← +OK
→ {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

- **query**: Execute a read-only SQL query
  - Input: `sql` (string) - The SQL query to execute
  - All queries run within a READ ONLY transaction

- **list_tables**: List all tables in the public schema
  - Returns list of table names

- **get_table_schema**: Get column information for a table
  - Input: `table_name` (string) - Name of the table
  - Returns column names and data types

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
    ["postgres-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {"DB_HOST": "localhost", "DB_USER": "app", "DB_PASS": "secret", "DB_NAME": "mydb"}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## Security

- Credentials exist only in process memory
- No environment variables exposed in `/proc/<pid>/environ`
- No CLI arguments visible in `ps aux`
- No credentials written to disk
- Parent process controls credential distribution

## License

MIT
