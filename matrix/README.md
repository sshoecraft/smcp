# Matrix SMCP Server

An MCP server for the Matrix protocol with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides Matrix messaging and room management capabilities via the Model Context Protocol (MCP). Unlike traditional MCP servers that receive credentials via command-line arguments or environment variables, this server uses SMCP for secure credential injection at startup.

## Features

- **Secure Credentials**: Receives homeserver URL and access token via SMCP handshake (no CLI args, no env vars, no disk)
- **Messaging**: Send plain text and HTML messages, read message history, react, and redact
- **Room Management**: List, join, leave, create rooms; set topics and inspect room state
- **User Operations**: Invite users, list room members, view profiles, set display name

## SMCP Credentials

The server accepts the following credentials via SMCP JSON:

| Credential | Required | Description |
|------------|----------|-------------|
| `MATRIX_HOMESERVER` | Yes | Homeserver URL (e.g., `https://matrix.org`) |
| `MATRIX_ACCESS_TOKEN` | Yes | Access token for authentication |
| `MATRIX_USER_ID` | No | User ID (e.g., `@user:matrix.org`); auto-detected if omitted |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |

### Obtaining an Access Token

You can generate an access token by logging in via the Matrix client-server API:

```bash
curl -X POST https://matrix.example.com/_matrix/client/v3/login \
  -H "Content-Type: application/json" \
  -d '{"type":"m.login.password","user":"@user:example.com","password":"..."}'
```

The response contains an `access_token` field.

## Quick Start with Shepherd

```bash
shepherd smcp add matrix --command "matrix-smcp-server" --credential "MATRIX_HOMESERVER=https://matrix.example.com" --credential "MATRIX_ACCESS_TOKEN=syt_..."
```

## Usage

```bash
matrix-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"MATRIX_HOMESERVER":"https://matrix.example.com","MATRIX_ACCESS_TOKEN":"syt_..."}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### Messaging

#### send_message

Send a plain text message to a room.

**Parameters:**
- `room_id` (string, required): Room ID (e.g., `!abc123:matrix.org`)
- `body` (string, required): Message text

**Returns:** `{success, event_id, room_id}`

#### send_html_message

Send an HTML-formatted message with a plain text fallback.

**Parameters:**
- `room_id` (string, required): Room ID
- `body` (string, required): Plain text fallback
- `html` (string, required): HTML-formatted message body

**Returns:** `{success, event_id, room_id}`

#### read_messages

Read recent messages from a room.

**Parameters:**
- `room_id` (string, required): Room ID
- `limit` (integer, optional): Maximum messages to return (default: 20)

**Returns:** `{success, room_id, message_count, messages}` where messages is a JSON array of `{sender, event_id, timestamp, body, type}`

#### send_reaction

React to a message with an emoji or text.

**Parameters:**
- `room_id` (string, required): Room ID containing the message
- `event_id` (string, required): Event ID of the message to react to
- `reaction` (string, required): Reaction key (e.g., an emoji)

**Returns:** `{success, event_id, room_id}`

#### redact_message

Redact (delete) a message. The event remains but content is removed.

**Parameters:**
- `room_id` (string, required): Room ID containing the message
- `event_id` (string, required): Event ID of the message to redact
- `reason` (string, optional): Reason for the redaction

**Returns:** `{success, event_id, room_id}`

### Rooms

#### list_rooms

List all rooms the authenticated user has joined.

**Parameters:** None

**Returns:** `{success, room_count, rooms}` where rooms is a JSON array of `{room_id, name, topic, member_count}`

#### join_room

Join a room by ID or alias.

**Parameters:**
- `room_id` (string, required): Room ID (`!abc123:matrix.org`) or alias (`#room:matrix.org`)

**Returns:** `{success, room_id}`

#### leave_room

Leave a room.

**Parameters:**
- `room_id` (string, required): Room ID to leave

**Returns:** `{success, room_id, status}`

#### create_room

Create a new room.

**Parameters:**
- `name` (string, optional): Room name
- `topic` (string, optional): Room topic
- `invite` (string, optional): Comma-separated user IDs to invite
- `is_direct` (boolean, optional): Direct message room (default: false)
- `public` (boolean, optional): Publicly visible room (default: false)

**Returns:** `{success, room_id}`

#### set_room_topic

Set a room's topic.

**Parameters:**
- `room_id` (string, required): Room ID
- `topic` (string, required): New topic text

**Returns:** `{success, event_id, room_id}`

#### get_room_state

Get room state (name, topic, join rules, creator, etc.).

**Parameters:**
- `room_id` (string, required): Room ID

**Returns:** `{success, state}` where state is a JSON object with `room_id`, `name`, `topic`, `alias`, `creator`, `join_rule`, etc.

### Users

#### invite_user

Invite a user to a room.

**Parameters:**
- `room_id` (string, required): Room ID
- `user_id` (string, required): User ID to invite (e.g., `@user:matrix.org`)

**Returns:** `{success, room_id, user_id, status}`

#### get_room_members

Get all members of a room.

**Parameters:**
- `room_id` (string, required): Room ID

**Returns:** `{success, room_id, member_count, members}` where members is a JSON array of `{user_id, display_name, avatar_url}`

#### get_user_profile

Get a user's profile information.

**Parameters:**
- `user_id` (string, required): User ID (e.g., `@user:matrix.org`)

**Returns:** `{success, user_id, display_name, avatar_url}`

#### set_display_name

Set the authenticated user's display name.

**Parameters:**
- `display_name` (string, required): New display name

**Returns:** `{success, display_name, status}`

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
    ["matrix-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "MATRIX_HOMESERVER": "https://matrix.example.com",
    "MATRIX_ACCESS_TOKEN": "syt_your_access_token_here"
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
- No CLI arguments visible in `ps aux`
- No credentials written to disk
- Parent process controls credential distribution
- Access tokens should be scoped with minimal required permissions

## License

MIT
