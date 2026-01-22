# SMCP: Secure MCP Credential Protocol

**Version:** 0.1  
**Status:** Draft  
**Author:** Steve  

## Overview

SMCP defines a minimal protocol for injecting credentials into MCP servers at startup via stdin/stdout. The parent process holds credentials (from MSI, Vault, etc.); child MCP servers receive only what they need, with no credentials in environment variables, CLI args, or config files.

## Goals

- **Simple:** Implementable in <50 lines of code
- **Secure:** Credentials never touch disk or environment
- **Universal:** No dependencies, any language
- **Auditable:** Parent controls exactly what each child receives

## Transport

- **Downstream (parent → child):** stdin
- **Upstream (child → parent):** stdout
- **Framing:** Line-based, UTF-8, `\n` terminated

## Handshake

```
Child  → Parent:  +READY\n
Parent → Child:   +CRED\n
Parent → Child:   <key>=<value>\n   (repeated)
Parent → Child:   +END\n
Child  → Parent:  +OK <count>\n | +ERR <message>\n
(stdin closed, child proceeds with MCP initialization)
```

## Messages

| Message | Direction | Description |
|---------|-----------|-------------|
| `+READY` | C→P | Child is ready to receive credentials |
| `+CRED` | P→C | Begin credential block |
| `<key>=<value>` | P→C | Single credential (one per line) |
| `+END` | P→C | End credential block |
| `+OK <n>` | C→P | Acknowledged, received n credentials |
| `+ERR <msg>` | C→P | Error, with human-readable reason |

## Value Encoding

- Plain text: `API_KEY=sk-abc123`
- Base64 (for special chars): `PASSWORD=b64:cGFzc3dvcmQ=`
- Child decodes `b64:` prefix automatically

## Timeouts

| Event | Timeout | Behavior |
|-------|---------|----------|
| Child waits for `+CRED` after `+READY` | 5s | Emit `+ERR TIMEOUT`, exit 1 |
| Parent waits for `+READY` | 10s | Kill child, log failure |
| Parent waits for `+OK`/`+ERR` | 5s | Kill child, log failure |

## Example

```
← +READY
→ +CRED
→ DB_HOST=postgres.local
→ DB_USER=app
→ DB_PASS=b64:aHVudGVyMg==
→ AZURE_STORAGE_KEY=b64:eHl6MTIz...
→ +END
← +OK 4
(stdin closed)
(child initializes MCP transport)
```

## Child Implementation (Pseudocode)

```
print("+READY\n")
flush(stdout)

line = readline(stdin, timeout=5s)
if line != "+CRED":
    die("+ERR EXPECTED_CRED")

creds = {}
while true:
    line = readline(stdin, timeout=5s)
    if line == "+END":
        break
    key, value = split(line, "=", 1)
    if value.startswith("b64:"):
        value = base64_decode(value[4:])
    creds[key] = value

print("+OK " + len(creds) + "\n")
flush(stdout)
close(stdin)

# Proceed with normal MCP initialization using creds
```

## Parent Implementation (Pseudocode)

```
child = spawn("mcp-server --config smcp", stdin=PIPE, stdout=PIPE)

line = child.readline(timeout=10s)
if line != "+READY":
    kill(child)
    die("child didn't send +READY")

child.write("+CRED\n")
for key, value in credentials:
    if needs_encoding(value):
        value = "b64:" + base64_encode(value)
    child.write(key + "=" + value + "\n")
child.write("+END\n")
child.flush()

line = child.readline(timeout=5s)
if not line.startswith("+OK"):
    kill(child)
    die("credential injection failed: " + line)

child.stdin.close()
# Child now runs normal MCP protocol on stdin/stdout
```

## Security Considerations

1. **Credential Scope:** Parent should inject minimum required credentials per child (least privilege)
2. **Memory Hygiene:** Child should zero credential memory after copying to final destination
3. **No Persistence:** Child must never write credentials to disk
4. **Audit Logging:** Parent should log which credentials were sent to which child (keys only, not values)
5. **Stdin Closure:** Child must close stdin after `+OK` to prevent further injection

## MCP Integration

After SMCP handshake completes:
- Child's stdin is closed (no longer used for SMCP)
- MCP transport initializes on a new channel (per MCP spec)
- Typically: MCP uses fresh stdin/stdout or HTTP

**Option A:** MCP over stdout (stdin closed)  
**Option B:** MCP over HTTP (child binds port, parent connects)  
**Option C:** MCP over Unix socket

## Future Extensions

- `+VERSION <n>` — Protocol version negotiation
- `+REFRESH` — Mid-flight credential rotation (requires keeping stdin open)
- `+AUDIT <id>` — Correlation ID for logging

---

## Quick Reference

```
Child                          Parent
  │                              │
  │◄──────── spawn ──────────────│
  │                              │
  ├─── +READY ──────────────────►│
  │                              │
  │◄───────────────── +CRED ─────┤
  │◄───────────────── K=V ───────┤
  │◄───────────────── K=V ───────┤
  │◄───────────────── +END ──────┤
  │                              │
  ├─── +OK 2 ───────────────────►│
  │                              │
  │  (stdin closed)              │
  │                              │
  │  [MCP protocol begins]       │
  ▼                              ▼
```
