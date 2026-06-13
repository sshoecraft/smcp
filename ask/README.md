# Ask SMCP Server

An MCP server that exposes one external LLM provider (Gemini, OpenAI Chat-Completions, or Anthropic Messages) as a single `query` tool. SMCP-enabled — credentials arrive via the SMCP handshake (Shepherd) or via environment variables (`--insecure` for clients like Claude Code).

## Overview

One running instance of `ask-smcp-server` is bound to one vendor + one model. It registers a single MCP tool, `query`. To expose more than one model to the calling client, register the same binary multiple times under different names; each registration runs its own process with its own credentials.

For example, `claude mcp add ask_gemini -- ask-smcp-server --insecure` surfaces the tool to the model as `mcp__ask_gemini__query`.

## Credentials

Same keys whether passed via SMCP handshake (Shepherd) or env (Claude Code `--insecure`).

| Key             | Required | Notes |
|-----------------|----------|-------|
| `ASK_TYPE`      | yes      | `gemini`, `openai`, or `anthropic` |
| `ASK_API_KEY`   | yes      | vendor API key |
| `ASK_MODEL`     | no       | overrides the type's default model |
| `ASK_BASE_URL`  | no       | overrides vendor endpoint (lets `openai` cover Grok/xAI, vLLM, etc.) |
| `ASK_MAX_TOKENS`| no       | default max_output_tokens per response, fallback 65536. Reasoning models (e.g. Gemini 3.x Pro) consume hidden "thought" tokens against this cap — keep it generous. |
| `ASK_SYSTEM`    | no       | default system prompt |
| `ASK_TIMEOUT`   | no       | HTTP request timeout in seconds, default 600. Deep reasoning calls can take minutes. |
| `ASK_THINKING_LEVEL` | no  | Gemini-only. Thinking effort: `minimal`, `low`, `medium`, `high` (default `high`). Tune down to reclaim visible-output budget. |
| `ASK_REASONING_EFFORT` | no | OpenAI reasoning models only (`gpt-5`/o-series). Reasoning effort: `minimal`, `low`, `medium`, `high` (default unset → model default). Ignored for non-reasoning models. Tune down to reclaim visible-output budget. |
| `ASK_AUTO_CONTINUE` | no   | All vendors. If the response hits the output cap (`MAX_TOKENS`/`length`/`max_tokens`) with visible text, issue a single bounded continuation call (default `1`). Set `0` to disable. Cap is one retry per ask — worst case 2 API calls. |
| `LOG_LEVEL`     | no       | default INFO |

### Defaults per type

| Type        | Default model               |
|-------------|-----------------------------|
| `gemini`    | `gemini-3.1-flash-lite`     |
| `openai`    | `gpt-5.4-nano`              |
| `anthropic` | `claude-haiku-4-5`          |

## MCP tool

- **`query`** — send a prompt and get a reply.
  - `prompt` (string, required) — the question/task
  - `system` (string, optional) — overrides `ASK_SYSTEM`
  - `model` (string, optional) — per-call model override
  - `max_tokens` (number, optional) — per-call cap override
  - Returns on success: `{"success": "true", "content": "...", "model": "...", "finish_reason": "STOP|MAX_TOKENS|length|stop|end_turn|max_tokens|...", "continuations": "0|1", "prompt_tokens": "N", "output_tokens": "N", "thoughts_tokens": "N", "total_tokens": "N"}`. All vendors return `finish_reason`, `continuations`, and the token counts (`thoughts_tokens` = Gemini thoughts / OpenAI reasoning tokens; Anthropic reports `0` since it bills thinking inside `output_tokens` and exposes no separate count). `continuations=1` means an auto-continuation fired.
  - Returns on failure: `{"success": "false", "error": "...", "model": "..."}`.

The tool description rendered to the calling model includes the resolved vendor and model so the caller knows which backend it is hitting.

## Usage with Claude Code (`--insecure`, env-var transport)

```
claude mcp add ask_gemini -- ask-smcp-server --insecure
  env: ASK_TYPE=gemini ASK_API_KEY=AIza...

claude mcp add ask_opus -- ask-smcp-server --insecure
  env: ASK_TYPE=anthropic ASK_API_KEY=sk-ant-... ASK_MODEL=claude-opus-4-7

claude mcp add ask_grok -- ask-smcp-server --insecure
  env: ASK_TYPE=openai ASK_API_KEY=xai-... ASK_MODEL=grok-2-latest ASK_BASE_URL=https://api.x.ai/v1
```

Tools surfaced to the model:

```
mcp__ask_gemini__query
mcp__ask_opus__query
mcp__ask_grok__query
```

## Usage with Shepherd (proper SMCP — no env vars, no disk)

```
shepherd smcp add ask_gemini ask-smcp-server \
    --cred ASK_TYPE=gemini --cred ASK_API_KEY=AIza...

shepherd smcp add ask_opus ask-smcp-server \
    --cred ASK_TYPE=anthropic --cred ASK_API_KEY=sk-ant-... \
    --cred ASK_MODEL=claude-opus-4-7

shepherd smcp add ask_grok ask-smcp-server \
    --cred ASK_TYPE=openai --cred ASK_API_KEY=xai-... \
    --cred ASK_MODEL=grok-2-latest \
    --cred ASK_BASE_URL=https://api.x.ai/v1
```

Same binary, same credential keys; Shepherd injects them via the SMCP handshake on stdin instead of through the environment.

## Building

```
pip install -e ../lib   # install the shared smcp library first
pip install -e .
```

Or from the repo root: `make install` (handles both).

## Security

- Credentials live only in process memory (under SMCP) or in environment (under `--insecure`)
- No CLI args, no disk persistence, no logging of credential values
- Parent process controls credential distribution under SMCP

## License

MIT
