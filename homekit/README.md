# HomeKit SMCP Server

An MCP server for HomeKit devices with SMCP (Secure MCP Credential Protocol) support for secure credential injection. Control any HomeKit device locally without cloud dependencies.

## Overview

This server provides local control of HomeKit devices via the Model Context Protocol (MCP). It communicates directly with devices on your local network using the HomeKit Accessory Protocol (HAP) - no Apple ID or cloud services required.

## Features

- **Local Control**: Direct communication with devices on your LAN
- **No Cloud**: Works without internet connection after initial pairing
- **Secure Credentials**: Receives pairing data via SMCP handshake
- **Generic Device Support**: Control any HomeKit-compatible device
- **Device-Specific Tools**: Convenient shortcuts for lights, thermostats, and sensors
- **Read-Only Mode**: Optional read-only mode for safe monitoring

## SMCP Credentials

| Credential | Required | Description |
|------------|----------|-------------|
| `HOMEKIT_PAIRING_DATA` | Yes | JSON pairing data from `homekit-smcp-pair` utility |
| `READ_ONLY_MODE` | No | "true" or "false" (default: "false") |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR (default: "INFO") |

## Quick Start with Shepherd

```bash
shepherd smcp add homekit --command "homekit-smcp-server" --credential 'HOMEKIT_PAIRING_DATA={"AccessoryPairingID":"...","AccessoryLTPK":"...","iOSPairingId":"...","iOSDeviceLTSK":"...","iOSDeviceLTPK":"...","AccessoryIP":"192.168.1.x","AccessoryPort":21063}'
```

## Initial Setup: Pairing

Before using the SMCP server, you must pair with your HomeKit device using the included utility.

### 1. Discover Devices

```bash
homekit-smcp-pair --discover
```

Output:
```
Found 2 HomeKit device(s):

Device 1:
  Name:        Living Room Light
  ID:          AA:BB:CC:DD:EE:FF
  Model:       LIFX A19
  Status:      Unpaired
  Address:     192.168.1.50:8080
```

### 2. Pair with Device

```bash
homekit-smcp-pair --pair --device-id AA:BB:CC:DD:EE:FF --pin 123-45-678
```

The PIN is the 8-digit HomeKit setup code printed on your device or in its documentation.

### 3. Save Pairing Data

```bash
homekit-smcp-pair --pair --device-id AA:BB:CC:DD:EE:FF --pin 12345678 --output pairing.json
```

The output JSON is your `HOMEKIT_PAIRING_DATA` credential.

## Usage

```bash
homekit-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"HOMEKIT_PAIRING_DATA":"{\"alias\":\"light\",\"AccessoryPairingID\":\"AA:BB:CC:DD:EE:FF\",...}","READ_ONLY_MODE":"false"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Generic Tools

- **list_accessories**: List all accessories with services and characteristics
- **get_accessory_info**: Get device info (name, manufacturer, model)
- **get_characteristics**: Read specific characteristic values by aid/iid
- **set_characteristics**: Write characteristic values (requires write permission)

### Light Tools

- **get_light**: Get light state (on/off, brightness, color)
- **set_light**: Control light (on/off, brightness 0-100, hue 0-360, saturation 0-100)
- **turn_on_light**: Turn on a light
- **turn_off_light**: Turn off a light

### Climate Tools

- **get_thermostat**: Get thermostat state (temperatures, mode)
- **set_thermostat**: Set target temperature and/or mode
- **set_thermostat_mode**: Set mode (off, heat, cool, auto)

### Sensor Tools

- **get_sensors**: Get all sensor values from an accessory
- **get_temperature_sensor**: Get temperature reading
- **get_humidity_sensor**: Get humidity reading
- **get_motion_sensor**: Check motion detection
- **get_contact_sensor**: Check door/window contact state

## Building

```bash
pip install -e ../lib  # Install shared smcp library
pip install -e .
```

## Supported Devices

Any device that supports HomeKit can be controlled, including:

- **Lights**: Bulbs, switches, dimmers, LED strips
- **Climate**: Thermostats, fans, air purifiers
- **Sensors**: Temperature, humidity, motion, contact, leak, smoke
- **Locks**: Smart locks (with appropriate permissions)
- **Covers**: Blinds, shades, garage doors

## HomeKit Limitations

HomeKit exposes a standardized interface, not vendor-specific features:

- Thermostat fan control is not available via HomeKit
- Remote sensors (like ecobee room sensors) are not exposed
- Schedules and programs are not accessible
- Only characteristics defined in the HAP spec are available

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

# Load pairing data from file
with open("pairing.json") as f:
    pairing_data = f.read()

child = subprocess.Popen(
    ["homekit-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "HOMEKIT_PAIRING_DATA": pairing_data,
    "READ_ONLY_MODE": "false"
}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## Security

- Pairing data contains cryptographic keys - treat it like a password
- Credentials exist only in process memory during runtime
- No cloud services or internet required after pairing
- Communication is encrypted using HomeKit's session security

## License

MIT
