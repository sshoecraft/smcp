# SMCP: Secure MCP Credential Protocol

A minimal protocol for securely injecting credentials into MCP servers at startup via stdin/stdout.

## Problem

MCP servers typically receive credentials through:
- Environment variables → visible in `/proc/<pid>/environ`, `docker inspect`
- CLI arguments → visible in `ps aux`
- Config files → persisted to disk

All of these leak credentials.

## Solution

SMCP defines a simple handshake where a parent process (with access to MSI, Vault, etc.) injects credentials into child MCP servers at startup. Credentials exist only in process memory.

```
Child  → Parent:  +READY
Parent → Child:   {"DB_PASS":"secret","API_KEY":"sk-123"}
Child  → Parent:  +OK
── MCP JSON-RPC begins ──
```

## Features

- **Simple:** 3 messages, implementable in <10 lines
- **Secure:** No env vars, no CLI args, no disk
- **Universal:** Uses built-in JSON parsers (every language has one)
- **Auditable:** Parent controls credential distribution

## Specification

See [SPEC.md](SPEC.md) for the full protocol specification.

## License

MIT
