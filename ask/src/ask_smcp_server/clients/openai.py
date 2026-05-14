"""OpenAI Chat-Completions client (also serves Grok/xAI, vLLM, etc. via ASK_BASE_URL)."""

from typing import Any, Dict

import httpx

from ask_smcp_server.clients.base import http_error_text


async def ask(
    config,
    http: httpx.AsyncClient,
    prompt: str,
    system: str,
    model: str,
    max_tokens: int,
) -> Dict[str, Any]:
    url = f"{config.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
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
    choices = data.get("choices") or []
    if not choices:
        return {"success": "false", "error": f"OpenAI returned no choices: {data}", "model": model}

    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        finish = choices[0].get("finish_reason", "unknown")
        return {"success": "false", "error": f"OpenAI returned empty content (finish_reason={finish})", "model": model}

    return {"success": "true", "content": content, "model": model}
