# EcoNet SMCP Server

An MCP server for Rheem EcoNet water heaters and thermostats with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides control of Rheem EcoNet devices via the Model Context Protocol (MCP). It uses a self-contained implementation of the Rheem/ClearBlade API for both REST (authentication, equipment discovery) and MQTT (device control, real-time updates). Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Architecture

The server implements the EcoNet/ClearBlade API directly:

- **REST API** (`rheem.clearblade.com`): Authentication, equipment discovery, usage reports
- **MQTT** (port 1884, TLS): Real-time device state updates and control commands

### API Protocol

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v/1/user/auth` | Login with email/password |
| `POST /api/v/1/code/{system_key}/getUserDataForApp` | Get equipment list |
| `POST /api/v/1/code/{system_key}/dynamicAction` | Get usage reports |
| MQTT `user/{account_id}/device/reported` | Device state updates (subscribe) |
| MQTT `user/{account_id}/device/desired` | Control commands (publish) |

## Features

- **Self-Contained**: No external dependencies on pyeconet or other EcoNet libraries
- **Secure Credentials**: Receives EcoNet credentials via SMCP handshake (no CLI args, no env vars, no disk)
- **Water Heater Control**: Get status, set mode, set temperature, get energy/water usage
- **Thermostat Status**: Get thermostat status (mode, setpoints, humidity)
- **Real-time Updates**: MQTT subscription for live device state changes

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `ECONET_EMAIL` | Yes | Rheem EcoNet account email |
| `ECONET_PASSWORD` | Yes | Rheem EcoNet account password |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add econet --command "econet-smcp-server" --credential "ECONET_EMAIL=user@example.com" --credential "ECONET_PASSWORD=..."
```

## Usage

```bash
econet-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"ECONET_EMAIL":"user@example.com","ECONET_PASSWORD":"secret"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Equipment Discovery

#### list_equipment
List all EcoNet equipment (water heaters and thermostats).

**Returns:** `{success, count, equipment}` where equipment is a JSON array

### Water Heater Tools

#### get_water_heater
Get water heater status.

**Parameters:**
- `device_id` (string, optional): Device ID. If not provided, uses the first water heater.

**Returns:** `{success, data}` where data includes:
- `device_id`, `name`, `serial_number`
- `mode`, `mode_index`, `available_modes`
- `setpoint`, `setpoint_min`, `setpoint_max`
- `enabled`, `running`, `running_status`
- `hot_water_level` (0-100%)
- `connected`

#### set_water_heater_mode
Set water heater operation mode.

**Parameters:**
- `mode` (string, required): Operation mode
- `device_id` (string, optional): Device ID

**Valid Modes** (varies by device):
- `OFF` - Turn off
- `ENERGY_SAVING` / `ENERGY_SAVER` - Energy saver mode
- `HEAT_PUMP_ONLY` / `HEAT_PUMP` - Heat pump only (most efficient)
- `HIGH_DEMAND` - High demand mode
- `ELECTRIC` / `ELECTRIC_MODE` - Electric heating only
- `PERFORMANCE` - Performance mode
- `VACATION` - Vacation mode

#### set_water_heater_temperature
Set water heater target temperature.

**Parameters:**
- `temperature` (integer, required): Target temperature in Fahrenheit (typically 90-140)
- `device_id` (string, optional): Device ID

#### get_water_heater_energy_usage
Get energy usage report for today.

**Parameters:**
- `device_id` (string, optional): Device ID

**Returns:** `{success, device_id, message, data}` with hourly breakdown

#### get_water_heater_water_usage
Get water usage report for today.

**Parameters:**
- `device_id` (string, optional): Device ID

**Returns:** `{success, device_id, data}` with hourly breakdown

### Thermostat Tools

#### get_thermostat
Get thermostat status.

**Parameters:**
- `device_id` (string, optional): Device ID

**Returns:** `{success, data}` where data includes:
- `device_id`, `name`, `serial_number`
- `mode`, `mode_index`, `available_modes`
- `heat_setpoint`, `cool_setpoint`
- `humidity`, `fan_mode`, `fan_speed`
- `enabled`, `running`, `running_status`
- `connected`

## Building

```bash
pip install -e ../lib      # Install shared smcp library
pip install -e .
```

## Dependencies

- `mcp>=1.6.0` - Model Context Protocol
- `smcp` - SMCP handshake library
- `requests>=2.28.0` - REST API calls
- `paho-mqtt>=2.0.0` - MQTT for device control

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

child = subprocess.Popen(
    ["econet-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {"ECONET_EMAIL": "user@example.com", "ECONET_PASSWORD": "secret"}
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

## Version History

- **0.2.0** - Self-contained implementation (no pyeconet dependency)
- **0.1.0** - Initial release with pyeconet wrapper

## License

MIT
