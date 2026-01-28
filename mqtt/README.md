# MQTT SMCP Server

An MCP server for MQTT with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides generic MQTT publish/subscribe capabilities via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives broker credentials via SMCP handshake (no CLI args, no env vars, no disk)
- **Publish/Subscribe**: Full MQTT pub/sub with wildcard support
- **Retained Messages**: Retrieve retained messages from topics
- **TLS Support**: Optional TLS encryption

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `MQTT_BROKER` | Yes | Broker hostname/IP (e.g., `mqtt.local`) |
| `MQTT_PORT` | No | Broker port (default: 1883) |
| `MQTT_USER` | No | Username for authentication |
| `MQTT_PASS` | No | Password for authentication |
| `MQTT_CLIENT_ID` | No | Client ID (default: auto-generated UUID) |
| `MQTT_TLS` | No | Enable TLS (`true`/`false`, default: false) |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add mqtt --command "mqtt-smcp-server" --credential "MQTT_BROKER=192.168.1.100" --credential "MQTT_PORT=1883" --credential "MQTT_USER=mqttuser" --credential "MQTT_PASS=..."
```

## Usage

```bash
mqtt-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"MQTT_BROKER":"mqtt.local","MQTT_USER":"user","MQTT_PASS":"secret"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### publish

Publish a message to an MQTT topic.

**Parameters:**
- `topic` (string, required): MQTT topic to publish to
- `message` (string, required): Message payload
- `retain` (boolean, optional): Retain the message (default: false)

**Returns:** `{success, topic, retain}`

### subscribe

Subscribe to a topic pattern and receive messages.

**Parameters:**
- `topic` (string, required): Topic pattern (supports `+` and `#` wildcards)
- `timeout` (float, optional): How long to wait for messages in seconds (default: 2.0)

**Returns:** `{success, message_count, messages}` where messages is a JSON array of `{topic, payload, retain, qos}`

### get_retained

Get retained messages from a topic pattern.

**Parameters:**
- `topic` (string, required): Topic pattern (supports `+` and `#` wildcards)
- `timeout` (float, optional): How long to wait in seconds (default: 1.0)

**Returns:** `{success, message_count, messages}` where messages is a JSON array of retained messages

### unsubscribe

Unsubscribe from a topic.

**Parameters:**
- `topic` (string, required): Topic to unsubscribe from

**Returns:** `{success, topic}`

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
    ["mqtt-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {"MQTT_BROKER": "localhost", "MQTT_USER": "user", "MQTT_PASS": "secret"}
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
