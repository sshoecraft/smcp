"""Anthropic Messages client."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ask_smcp_server.clients.base import http_error_text

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"

CONTINUE_PROMPT = (
    "Continue from exactly where you left off. "
    "Do not repeat anything you already wrote. "
    "Do not summarize. Do not preface. Just continue."
)


def _build_body(
    model: str,
    system: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
) -> Dict[str, Any]:
    return {
        "model": model,
        "system": system,
        "messages": messages,
        "max_tokens": max_tokens,
    }


def _extract(data: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
    """Return (text, stop_reason, usage) with Gemini/OpenAI-compatible usage keys."""
    blocks = data.get("content") or []
    text_chunks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    text = "".join(text_chunks)

    stop_reason = data.get("stop_reason") or "unknown"

    usage_raw = data.get("usage") or {}
    prompt_tokens = int(usage_raw.get("input_tokens", 0))
    output_tokens = int(usage_raw.get("output_tokens", 0))
    # Anthropic does not break out a separate thinking-token count (extended
    # thinking is billed inside output_tokens) and returns no total, so report
    # thoughts_tokens=0 and compute the total from input + output.
    usage = {
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "thoughts_tokens": 0,
        "total_tokens": prompt_tokens + output_tokens,
    }
    return text, stop_reason, usage


async def _post(
    config,
    http: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """POST to the messages endpoint, return (json_data, error_text)."""
    try:
        response = await http.post(url, headers=headers, json=body, timeout=config.timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return None, http_error_text(exc)
    except httpx.HTTPError as exc:
        return None, str(exc)
    return response.json(), None


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

    messages: List[Dict[str, str]] = [
        {"role": "user", "content": prompt},
    ]

    body = _build_body(model, system, messages, max_tokens)
    data, err = await _post(config, http, url, headers, body)
    if err is not None:
        return {"success": "false", "error": err, "model": model}

    content, stop_reason, usage = _extract(data)
    continuations = 0

    # stop_reason == "max_tokens" means the output cap was hit and the reply is
    # truncated mid-thought. Recover the tail with a single bounded continuation
    # (worst case: 2 calls). If there is no visible text there is nothing to
    # continue from, so fall through to the error below.
    if stop_reason == "max_tokens" and config.auto_continue and content.strip():
        logger.info(
            f"Anthropic max_tokens hit (output={usage.get('output_tokens')}); "
            f"issuing single continuation"
        )
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": CONTINUE_PROMPT})

        body = _build_body(model, system, messages, max_tokens)
        data2, err2 = await _post(config, http, url, headers, body)
        if err2 is not None:
            logger.warning(f"Continuation failed: {err2}")
        else:
            content2, stop_reason2, usage2 = _extract(data2)
            if content2.strip():
                content += content2
                continuations = 1
                stop_reason = stop_reason2
                for key in usage:
                    usage[key] += usage2.get(key, 0)

    content = content.strip()
    if not content:
        return {
            "success": "false",
            "error": f"Anthropic returned no text content (stop_reason={stop_reason})",
            "model": model,
            "finish_reason": stop_reason,
            "continuations": continuations,
            **usage,
        }

    return {
        "success": "true",
        "content": content,
        "model": model,
        "finish_reason": stop_reason,
        "continuations": continuations,
        **usage,
    }
