# Ecobee SMCP Server

An MCP server for Ecobee thermostats with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Important: API Access Limitation

**As of March 2024, Ecobee is no longer accepting new developer registrations or issuing new API keys.** This server only works for users who already have API keys from before this change. There is no announced timeline for when Ecobee will reopen developer access.

If you don't already have an Ecobee API key, this server will not work for you.

## Overview

This server provides access to Ecobee thermostats via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via environment variables or config files, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives Ecobee API credentials via SMCP handshake (no env vars, no config files, no disk)
- **Full Thermostat Control**: Read temperature, sensors, settings; set temperature, mode, fan
- **Vacation Management**: Create and delete vacation events
- **Remote Sensors**: Access all remote sensor readings
- **Read-Only Mode**: Optional read-only mode for safe monitoring

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `ECOBEE_API_KEY` | Yes | Application key from ecobee developer portal |
| `ACCESS_TOKEN` | Yes | OAuth2 access token |
| `REFRESH_TOKEN` | Yes | OAuth2 refresh token |
| `THERMOSTAT_ID` | No | Default thermostat ID (12-digit identifier) |
| `READ_ONLY_MODE` | No | "true" or "false" (default: "true") |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR (default: "INFO") |

## Quick Start with Shepherd

```bash
shepherd smcp add ecobee --command "ecobee-smcp-server" --credential "ECOBEE_API_KEY=..." --credential "ACCESS_TOKEN=..." --credential "REFRESH_TOKEN=..." --credential "THERMOSTAT_ID=123456789012"
```

## Usage

```bash
ecobee-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"ECOBEE_API_KEY":"abc123","ACCESS_TOKEN":"token...","REFRESH_TOKEN":"refresh...","THERMOSTAT_ID":"123456789012"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Status Tools (Read-Only)

- **list_thermostats**: List all thermostats registered to the account
- **get_thermostat_info**: Get basic info including name, time, and location
- **get_temperature**: Get current temperature, humidity, and setpoints
- **get_sensors**: Get all remote sensor readings (temperature, humidity, occupancy)
- **get_runtime**: Get runtime data including HVAC activity history

### Settings Tools

- **get_settings**: Get all thermostat settings
- **get_program**: Get the schedule and climate definitions
- **set_temperature**: Set heat/cool setpoints with optional hold type and duration
- **set_mode**: Set HVAC mode (heat, cool, auto, off)
- **resume_program**: Cancel holds and return to regular schedule
- **set_fan_mode**: Set fan mode (auto, on) and min on time

### Event Tools

- **get_events**: Get all active events
- **get_vacations**: Get vacation events
- **create_vacation**: Create a vacation with temperature setpoints and dates
- **delete_vacation**: Delete a vacation by name

## Building

```bash
pip install -e ../lib  # Install shared smcp library
pip install -e .
```

## Getting Ecobee API Credentials

**Note: Ecobee closed new developer registrations in March 2024. These steps only work if you already have a developer account.**

1. Log in to the ecobee developer portal at https://www.ecobee.com/developers/
2. Use your existing API key from a previously created application
3. Use the PIN authorization flow to get access and refresh tokens
4. Find your thermostat ID in the ecobee app under "About"

If you don't have existing API credentials, consider using the HomeKit SMCP server instead - Ecobee thermostats support HomeKit and that integration is still available.

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

child = subprocess.Popen(
    ["ecobee-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "ECOBEE_API_KEY": "your-api-key",
    "ACCESS_TOKEN": "your-access-token",
    "REFRESH_TOKEN": "your-refresh-token",
    "THERMOSTAT_ID": "123456789012",
    "READ_ONLY_MODE": "false"
}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## Security

- Credentials exist only in process memory
- No environment variables exposed in `/proc/<pid>/environ`
- No config files written to disk
- Parent process controls credential distribution
- Automatic token refresh when access token expires

## License

MIT
