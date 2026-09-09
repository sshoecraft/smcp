---
name: ask-openai-gpt6-token-param
description: GPT-6 (gpt-6-astra) rejects max_tokens and needs max_completion_tokens; ask server gates this on a model-name prefix list that must be extended per f…
metadata:
  type: project
tags: [ask, openai, gpt-6, api]
---

# ask server: OpenAI token-parameter gating

`ask/src/ask_smcp_server/clients/openai.py::uses_max_completion_tokens()` decides
between `max_tokens` and `max_completion_tokens` from a **model-name prefix list**.
Every new OpenAI reasoning family must be added there or every call to it fails
outright:

```
Unsupported parameter: 'max_tokens' is not supported with this model.
Use 'max_completion_tokens' instead.
```

Verified live against `gpt-6-astra` on 2026-09-09: `max_completion_tokens` works,
`max_tokens` returns the 400 above. Current prefixes: `gpt-5`, `gpt-6`, `o1`, `o3`, `o4`.

## Documentation is not a substitute for probing the endpoint

`developers.openai.com/api/docs/models/gpt-6-astra`, read through a summarizer,
claimed gpt-6-astra "uses standard max_tokens". That was wrong. A two-line curl
against the real endpoint settled it in one call and costs nothing when it errors —
do that before writing the branch.

## reasoning_effort levels are per-family, not global

`VALID_REASONING_EFFORTS` in `config.py` holds the **union** of all vendor levels
(`minimal`, `low`, `medium`, `high`, `xhigh`, `max`) and lets the API reject the
ones a given model lacks. gpt-6 added `xhigh`/`max` and dropped `minimal`;
gpt-5/o-series have `minimal` but not `xhigh`. `max` is Responses-API only.
Do not tighten this to one model's list.

## Testing a new registration without restarting the MCP client

A newly-added `claude mcp add` server does not appear as a tool in the session that
added it. `ask/tests/stdio_query.py <registration-name> "<prompt>"` drives the server
over stdio using the credentials pulled from `claude mcp get`, so no key is typed on
a command line and the exact registered config is exercised.

## Install mode

The repo Makefile installs non-editable (`pip install ./pkg`, deliberately not `-e`),
but the live install on this box is still editable from an earlier run — source edits
take effect immediately here. After a `make install` they will not; re-run it to pick
up source changes.
