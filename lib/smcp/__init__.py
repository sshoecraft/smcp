"""SMCP (Secure MCP Credential Protocol) - Shared handshake implementation."""

import sys
import json
from typing import Dict

__version__ = "0.2.0"


def handshake() -> Dict[str, str]:
    """
    Perform SMCP handshake to receive credentials securely via stdin/stdout.

    Protocol (v0.2):
        Child  -> Parent:  +READY
        Parent -> Child:   {"key":"value",...}
        Child  -> Parent:  +OK
        -- stdin/stdout transitions to MCP JSON-RPC --

    Returns:
        Dict of credential key-value pairs

    Raises:
        RuntimeError: If handshake fails
    """
    # Send +READY
    print("+READY", flush=True)

    # Read JSON credentials
    line = sys.stdin.readline()
    if not line:
        print("+ERR NO_INPUT", flush=True)
        raise RuntimeError("No credentials received")

    try:
        creds = json.loads(line)
    except json.JSONDecodeError as e:
        print("+ERR INVALID_JSON", flush=True)
        raise RuntimeError(f"Invalid JSON: {e}")

    if not isinstance(creds, dict):
        print("+ERR INVALID_FORMAT", flush=True)
        raise RuntimeError("Credentials must be a JSON object")

    # Send +OK
    print("+OK", flush=True)

    return creds
