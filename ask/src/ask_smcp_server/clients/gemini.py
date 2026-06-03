"""Google Gemini client."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ask_smcp_server.clients.base import http_error_text

logger = logging.getLogger(__name__)

CONTINUE_PROMPT = (
    "Continue from exactly where you left off. "
    "Do not repeat anything you already wrote. "
    "Do not summarize. Do not preface. Just continue."
)


def _build_body(
    contents: List[Dict[str, Any]],
    system: str,
    max_tokens: int,
    thinking_level: str,
) -> Dict[str, Any]:
    return {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingLevel": thinking_level},
        },
    }


def _extract(data: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
    """Return (visible_text, finish_reason, usage)."""
    candidates = data.get("candidates") or []
    if not candidates:
        return "", "NO_CANDIDATES", {}

    cand = candidates[0]
    finish_reason = cand.get("finishReason", "UNKNOWN")
    parts = cand.get("content", {}).get("parts") or []
    text_chunks = [
        p.get("text", "")
        for p in parts
        if "text" in p and not p.get("thought")
    ]
    text = "".join(text_chunks)

    usage_raw = data.get("usageMetadata") or {}
    usage = {
        "prompt_tokens": int(usage_raw.get("promptTokenCount", 0)),
        "output_tokens": int(usage_raw.get("candidatesTokenCount", 0)),
        "thoughts_tokens": int(usage_raw.get("thoughtsTokenCount", 0)),
        "total_tokens": int(usage_raw.get("totalTokenCount", 0)),
    }
    return text, finish_reason, usage


async def _post(
    config,
    http: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """POST to Gemini, return (json_data, error_text)."""
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
    url = f"{config.base_url}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": config.api_key,
        "Content-Type": "application/json",
    }

    contents: List[Dict[str, Any]] = [
        {"role": "user", "parts": [{"text": prompt}]},
    ]

    body = _build_body(contents, system, max_tokens, config.thinking_level)
    data, err = await _post(config, http, url, headers, body)
    if err is not None:
        return {"success": "false", "error": err, "model": model}

    text, finish_reason, usage = _extract(data)
    continuations = 0

    if not text and finish_reason not in ("MAX_TOKENS",):
        return {
            "success": "false",
            "error": f"Gemini returned empty text (finishReason={finish_reason}, usage={usage})",
            "model": model,
            "finish_reason": finish_reason,
            **usage,
        }

    if finish_reason == "MAX_TOKENS" and config.auto_continue:
        logger.info(
            f"Gemini MAX_TOKENS hit (visible={usage.get('output_tokens')}, "
            f"thoughts={usage.get('thoughts_tokens')}); issuing single continuation"
        )
        contents.append({"role": "model", "parts": [{"text": text}]})
        contents.append({"role": "user", "parts": [{"text": CONTINUE_PROMPT}]})

        body = _build_body(contents, system, max_tokens, config.thinking_level)
        data2, err2 = await _post(config, http, url, headers, body)
        if err2 is not None:
            logger.warning(f"Continuation failed: {err2}")
        else:
            text2, finish_reason2, usage2 = _extract(data2)
            if text2:
                text += text2
                continuations = 1
                finish_reason = finish_reason2
                for key in usage:
                    usage[key] += usage2.get(key, 0)

    content = text.strip()
    if not content:
        return {
            "success": "false",
            "error": f"Gemini returned empty text (finishReason={finish_reason}, usage={usage})",
            "model": model,
            "finish_reason": finish_reason,
            "continuations": continuations,
            **usage,
        }

    return {
        "success": "true",
        "content": content,
        "model": model,
        "finish_reason": finish_reason,
        "continuations": continuations,
        **usage,
    }
