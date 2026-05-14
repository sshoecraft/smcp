"""Anthropic Messages client."""

from typing import Any, Dict

import httpx

from ask_smcp_server.clients.base import http_error_text


ANTHROPIC_VERSION = "2023-06-01"


async def ask(
    config,
    http: httpx.AsyncClient,
    prompt: str,
    system: str,
    model: str,
    max_tokens: int,
) -> Dict[str, Any]:
    url = f"{config.base_url}/messages"
    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "system": system,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
    }

    try:
        response = await http.post(url, headers=headers, json=body)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {"success": "false", "error": http_error_text(exc), "model": model}
    except httpx.HTTPError as exc:
        return {"success": "false", "error": str(exc), "model": model}

    data = response.json()
    blocks = data.get("content") or []
    text_chunks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    content = "".join(text_chunks).strip()
    if not content:
        stop = data.get("stop_reason", "unknown")
        return {"success": "false", "error": f"Anthropic returned no text content (stop_reason={stop})", "model": model}

    return {"success": "true", "content": content, "model": model}
