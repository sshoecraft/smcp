# Search SMCP Server

An MCP server that exposes a **local SearXNG instance** as a web-search tool, with SMCP (Secure MCP Credential Protocol) support for secure credential injection.

## Overview

[SearXNG](https://github.com/searxng/searxng) is a privacy-respecting metasearch engine you can self-host. This server lets an LLM client (Claude Desktop, Shepherd, etc.) query a SearXNG instance you specify by IP/port (or full URL) and get back trimmed, LLM-friendly JSON results.

## Features

- **Local SearXNG**: Point at any IP/host/port — your own LAN box, a Docker container, anything that speaks the SearXNG JSON API.
- **Secure Credentials**: Connection details delivered via the SMCP handshake (no CLI args, no env vars, no disk).
- **LLM-friendly Results**: Strips the SearXNG response down to title/url/content snippets, infoboxes, suggestions, and answers.
- **Engine Filters**: Constrain queries to specific engines, categories, languages, time ranges, or safesearch levels.
- **Engine Discovery**: List the engines configured on the instance.

## Prerequisites

Your SearXNG instance must have the `json` output format enabled. In `settings.yml`:

```yaml
search:
  formats:
    - html
    - json
```

## SMCP Credentials

| Credential | Required | Description |
|------------|----------|-------------|
| `SEARCH_HOST` | No | Hostname, IP, or full base URL (default: `localhost`; e.g. `192.168.1.10`, `searx.lan`, `http://searx.lan:8080`) |
| `SEARCH_PORT` | No | Port (default: 8888) — ignored if `SEARCH_HOST` is a full URL |
| `SEARCH_SSL` | No | Use HTTPS (`true`/`false`, default: false) — ignored if `SEARCH_HOST` is a full URL |
| `SEARCH_PATH` | No | Path prefix if SearXNG is reverse-proxied under a subpath (e.g. `searx`) |
| `SEARCH_USERNAME` | No | Basic-auth username, if the instance is protected |
| `SEARCH_PASSWORD` | No | Basic-auth password |
| `SEARCH_TIMEOUT` | No | HTTP timeout in seconds (default: 30) |
| `SEARCH_LANGUAGE` | No | Default language code (default: `en`) |
| `SEARCH_SAFESEARCH` | No | Default safesearch: 0 off, 1 moderate, 2 strict (default: 0) |
| `SEARCH_MAX_RESULTS` | No | Default cap on results returned per call (default: 10) |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR (default: INFO) |

## Quick Start with Shepherd

```bash
shepherd smcp add search \
    --command "search-smcp-server" \
    --credential "SEARCH_HOST=192.168.1.10" \
    --credential "SEARCH_PORT=8080"
```

Or with a full URL:

```bash
shepherd smcp add search \
    --command "search-smcp-server" \
    --credential "SEARCH_HOST=http://searx.lan:8080"
```

## MCP Tools

### search

Run a web search against the configured SearXNG instance.

**Parameters:**
- `query` (string, required): Search query.
- `categories` (string, optional): Comma-separated categories (`general`, `news`, `images`, `videos`, `it`, `science`, etc.).
- `engines` (string, optional): Comma-separated engine names (e.g. `google,bing,duckduckgo`).
- `language` (string, optional): Language code override.
- `pageno` (int, optional): 1-indexed result page.
- `time_range` (string, optional): `day`, `week`, `month`, or `year`.
- `safesearch` (int, optional): 0/1/2.
- `max_results` (int, optional): Cap on results returned.

**Returns:** `{success, data}` where `data` is a JSON-encoded object containing `query`, `result_count`, `results`, `infoboxes`, `suggestions`, and `answers`.

### list_engines

List the search engines configured on the SearXNG instance.

**Parameters:** None

**Returns:** `{success, count, engines}` where `engines` is a JSON-encoded array of `{name, categories, enabled, shortcut, timeout}` objects.

## Building

```bash
pip install -e ../lib   # shared smcp library
pip install -e .
```

Or from the repo root:

```bash
make
```

## Usage

```bash
search-smcp-server
```

The server performs the SMCP handshake on startup:

```
<- +READY
-> {"SEARCH_HOST":"192.168.1.10","SEARCH_PORT":"8080"}
<- +OK
-> {"jsonrpc":"2.0","method":"initialize",...}
(MCP JSON-RPC continues)
```

## Security

- Credentials exist only in process memory
- No environment variables exposed in `/proc/<pid>/environ`
- No CLI arguments visible in `ps aux`
- No credentials written to disk

## License

MIT
