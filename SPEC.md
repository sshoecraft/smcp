# SMCP: Secure MCP Credential Protocol

**Version:** 0.2  
**Status:** Draft  
**Author:** Steve  

## Overview

SMCP defines a minimal protocol for injecting credentials into MCP servers at startup via stdin/stdout. The parent process holds credentials (from MSI, Vault, etc.); child MCP servers receive only what they need, with no credentials in environment variables, CLI args, or config files.

## Goals

- **Simple:** Implementable in <10 lines of code
- **Secure:** Credentials never touch disk or environment
- **Universal:** No dependencies, uses built-in JSON parsers
- **Auditable:** Parent controls exactly what each child receives

## Transport

- **Downstream (parent → child):** stdin
- **Upstream (child → parent):** stdout
- **Framing:** Line-based, UTF-8, `\n` terminated
- **Credential format:** Single-line JSON object

## Handshake

```
Child  → Parent:  +READY\n
Parent → Child:   {"key":"value",...}\n
Child  → Parent:  +OK\n | +ERR <message>\n
── SMCP complete, stdin/stdout transitions to MCP JSON-RPC ──
```

## Messages

| Message | Direction | Description |
|---------|-----------|-------------|
| `+READY` | C→P | Child is ready to receive credentials |
| `{...}` | P→C | JSON object containing credentials |
| `+OK` | C→P | Acknowledged, transitioning to MCP |
| `+ERR <msg>` | C→P | Error, with human-readable reason |

## Disambiguation

- Lines starting with `+` are SMCP control messages
- Lines starting with `{` are credential payload (during handshake) or MCP JSON-RPC (after `+OK`)
- After child sends `+OK`, all stdin/stdout traffic is MCP JSON-RPC

## Timeouts

| Event | Timeout | Behavior |
|-------|---------|----------|
| Child waits for credentials after `+READY` | 5s | Emit `+ERR TIMEOUT\n`, exit 1 |
| Parent waits for `+READY` | 10s | Kill child, log failure |
| Parent waits for `+OK`/`+ERR` | 5s | Kill child, log failure |

## Example Session

```
← +READY
→ {"DB_HOST":"postgres.local","DB_USER":"app","DB_PASS":"hunter2"}
← +OK
→ {"jsonrpc":"2.0","method":"initialize","params":{},"id":1}
← {"jsonrpc":"2.0","result":{},"id":1}
```

## Child Implementation

**Python:**
```python
import sys, json

print("+READY", flush=True)

line = sys.stdin.readline()
try:
    creds = json.loads(line)
except:
    print("+ERR INVALID_JSON", flush=True)
    sys.exit(1)

print("+OK", flush=True)

# stdin/stdout now MCP JSON-RPC
start_mcp_server(creds)
```

**TypeScript:**
```typescript
import * as readline from 'readline';

const rl = readline.createInterface({ input: process.stdin });

console.log('+READY');

rl.once('line', (line) => {
    let creds;
    try {
        creds = JSON.parse(line);
    } catch {
        console.log('+ERR INVALID_JSON');
        process.exit(1);
    }
    console.log('+OK');
    
    // stdin/stdout now MCP JSON-RPC
    startMcpServer(creds);
});
```

## Parent Implementation

**Python:**
```python
import subprocess, json

child = subprocess.Popen(
    ["mcp-server", "--smcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

line = child.stdout.readline().strip()
if line != "+READY":
    child.kill()
    raise Exception("child didn't send +READY")

credentials = {"DB_HOST": "localhost", "DB_PASS": "secret"}
child.stdin.write(json.dumps(credentials) + "\n")
child.stdin.flush()

line = child.stdout.readline().strip()
if line != "+OK":
    child.kill()
    raise Exception(f"credential injection failed: {line}")

# Child now running MCP, proxy stdin/stdout as needed
```

## Security Considerations

1. **Credential Scope:** Parent should inject minimum required credentials per child (least privilege)
2. **Memory Hygiene:** Child should zero credential memory after copying to final destination
3. **No Persistence:** Child must never write credentials to disk
4. **Audit Logging:** Parent should log which credentials were sent to which child (keys only, not values)

## Parent Configuration Example

```json
{
    "smcp_servers": [
        {
            "name": "azure-storage",
            "command": "mcp-azure-storage",
            "args": ["--smcp"],
            "credentials": {
                "AZURE_STORAGE_ACCOUNT_NAME": "mystorageaccount",
                "AZURE_STORAGE_ACCOUNT_KEY": "secretkey"
            }
        },
        {
            "name": "database",
            "command": "mcp-postgres",
            "args": ["--smcp"],
            "credentials": {
                "DB_HOST": "postgres.azure.com",
                "DB_USER": "admin",
                "DB_PASS": "secret-password"
            }
        }
    ]
}
```

## Quick Reference

```
Child                          Parent
  │                              │
  │◄──────── spawn ──────────────│
  │                              │
  ├─── +READY ──────────────────►│
  │                              │
  │◄──────── {json} ─────────────┤
  │                              │
  ├─── +OK ─────────────────────►│
  │                              │
  │  ══════ MCP JSON-RPC ══════  │
  │                              │
  │◄──────── {jsonrpc} ──────────┤
  ├──────── {jsonrpc} ──────────►│
  ▼                              ▼
```
