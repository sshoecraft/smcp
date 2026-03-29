"""SMCP (Secure MCP Credential Protocol) - Shared handshake implementation."""

import os
import sys
import json
import logging
from typing import Dict, Any

__version__ = "0.3.0"

logger = logging.getLogger(__name__)


def print_credentials_schema(schema: Dict[str, Any]) -> None:
    """Print credentials schema as JSON and exit.

    Call this from a server's main() before the SMCP handshake
    when --credentials-schema is in sys.argv.

    Args:
        schema: Dict with 'required' and/or 'optional' keys.
                Each maps credential key names to description strings.

    Example:
        schema = {
            "required": {
                "API_KEY": "API authentication key"
            },
            "optional": {
                "LOG_LEVEL": "Logging level (default: INFO)"
            }
        }
    """
    print(json.dumps(schema, indent=2))
    sys.exit(0)


def check_credentials_schema(schema: Dict[str, Any]) -> None:
    """Check for --credentials-schema flag and print schema if present.

    Convenience function that checks sys.argv and calls
    print_credentials_schema if the flag is found.

    Args:
        schema: Credentials schema dict to print.
    """
    if "--credentials-schema" in sys.argv:
        print_credentials_schema(schema)


def is_insecure() -> bool:
    """Check if --insecure mode was requested via CLI args."""
    return "--insecure" in sys.argv


def handshake() -> Dict[str, str]:
    """
    Perform SMCP handshake to receive credentials securely via stdin/stdout.

    If --insecure is passed on the command line, the handshake is skipped
    and credentials are read from environment variables instead. This allows
    SMCP servers to run as standard MCP servers (e.g., with Claude Code).

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
    if is_insecure():
        logger.warning("Running in --insecure mode: credentials from environment variables")
        return dict(os.environ)

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
