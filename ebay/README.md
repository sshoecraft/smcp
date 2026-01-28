# eBay SMCP Server

An MCP server for the eBay Browse API with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

This server provides access to eBay's Browse API for searching listings and retrieving item details via the Model Context Protocol (MCP). Credentials are securely injected at startup using SMCP.

## Features

- **Secure Credentials**: Receives eBay API credentials via SMCP handshake
- **Flexible Search**: Configurable filters for buying options and condition
- **Item Details**: Retrieve full item information including descriptions and specifics
- **Token Caching**: Automatic OAuth2 token management with refresh

## SMCP Credentials

| Credential | Required | Description |
|------------|----------|-------------|
| `EBAY_CLIENT_ID` | Yes | eBay developer client ID |
| `EBAY_CLIENT_SECRET` | Yes | eBay developer client secret |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add ebay --command "ebay-smcp-server" --credential "EBAY_CLIENT_ID=..." --credential "EBAY_CLIENT_SECRET=..."
```

## Usage

```bash
ebay-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"EBAY_CLIENT_ID":"your-client-id","EBAY_CLIENT_SECRET":"your-client-secret"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## MCP Tools

### search

Search eBay listings with configurable filters.

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `query` | Yes | - | Search query string |
| `limit` | No | 10 | Max results (1-200) |
| `buying_options` | No | "all" | Filter: all, fixed_price, buy_it_now, auction, best_offer |
| `condition` | No | "any" | Filter: any, new, used |

**Note:** `buy_it_now` is an alias for `fixed_price`.

**Example Response:**

```json
{
  "success": "true",
  "count": "5",
  "results": [
    {
      "item_id": "v1|123456789|0",
      "title": "Example Item",
      "price": "29.99",
      "currency": "USD",
      "shipping": "FREE",
      "condition": "New",
      "url": "https://www.ebay.com/itm/...",
      "seller": {
        "username": "seller123",
        "feedback_score": 1500,
        "feedback_percent": "99.5"
      }
    }
  ]
}
```

### get_item

Get detailed information for a specific item.

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `item_id` | Yes | eBay item ID from search results |

**Returns:** Full item details including description, item specifics, shipping options, and images.

## Building

```bash
pip install -e ../lib  # Install shared smcp library
pip install -e .
```

## Getting eBay API Credentials

1. Go to https://developer.ebay.com/
2. Create a developer account
3. Create an application in the Developer Portal
4. Get your Client ID and Client Secret from the application keys

## Example Parent Process (SMCP Launcher)

```python
import subprocess
import json

child = subprocess.Popen(
    ["ebay-smcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Wait for +READY
assert child.stdout.readline().strip() == "+READY"

# Send credentials as JSON
creds = {
    "EBAY_CLIENT_ID": "your-client-id",
    "EBAY_CLIENT_SECRET": "your-client-secret"
}
child.stdin.write(json.dumps(creds) + "\n")
child.stdin.flush()

# Wait for +OK
assert child.stdout.readline().strip() == "+OK"

# MCP JSON-RPC begins on stdin/stdout
```

## Security

- Credentials exist only in process memory
- OAuth2 tokens are cached in memory with automatic refresh
- No credentials written to disk or exposed in environment

## License

MIT
