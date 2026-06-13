"""OpenAI Chat-Completions client (also serves Grok/xAI, vLLM, etc. via ASK_BASE_URL)."""

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


def uses_max_completion_tokens(model: str) -> bool:
    """GPT-5 family and o-series reasoning models reject max_tokens and require max_completion_tokens."""
    name = model.lower()
    if name.startswith(("gpt-5", "o1", "o3", "o4")):
        return True
    return False


def _build_body(
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
    reasoning_effort: Optional[str],
) -> Dict[str, Any]:
    is_reasoning = uses_max_completion_tokens(model)
    token_param = "max_completion_tokens" if is_reasoning else "max_tokens"
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        token_param: max_tokens,
    }
    # reasoning_effort is only valid for reasoning models; sending it to a plain
    # chat model (or many OpenAI-compatible backends) gets rejected.
    if is_reasoning and reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    return body


def _extract(data: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
    """Return (content, finish_reason, usage) with Gemini-compatible usage keys."""
    choices = data.get("choices") or []
    if not choices:
        return "", "NO_CHOICES", {}

    choice = choices[0]
    finish_reason = choice.get("finish_reason", "unknown")
    message = choice.get("message") or {}
    content = message.get("content") or ""

    usage_raw = data.get("usage") or {}
    details = usage_raw.get("completion_tokens_details") or {}
    usage = {
        "prompt_tokens": int(usage_raw.get("prompt_tokens", 0)),
        "output_tokens": int(usage_raw.get("completion_tokens", 0)),
        "thoughts_tokens": int(details.get("reasoning_tokens", 0)),
        "total_tokens": int(usage_raw.get("total_tokens", 0)),
    }
    return content, finish_reason, usage


async def _post(
    config,
    http: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """POST to the chat-completions endpoint, return (json_data, error_text)."""
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
    url = f"{config.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    reasoning_effort = getattr(config, "reasoning_effort", None)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    body = _build_body(model, messages, max_tokens, reasoning_effort)
    data, err = await _post(config, http, url, headers, body)
    if err is not None:
        return {"success": "false", "error": err, "model": model}

    content, finish_reason, usage = _extract(data)
    continuations = 0

    # finish_reason == "length" means the output cap was hit. For reasoning
    # models hidden reasoning tokens count against max_completion_tokens, so a
    # hard problem can truncate the visible answer mid-thought. Recover the tail
    # with a single bounded continuation (worst case: 2 calls). If content is
    # empty the budget was fully consumed by reasoning; retrying under the same
    # cap won't help, so fall through to the error below instead of continuing
    # from an empty assistant turn.
    if finish_reason == "length" and config.auto_continue and content.strip():
        logger.info(
            f"OpenAI length cap hit (output={usage.get('output_tokens')}, "
            f"reasoning={usage.get('thoughts_tokens')}); issuing single continuation"
        )
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": CONTINUE_PROMPT})

        body = _build_body(model, messages, max_tokens, reasoning_effort)
        data2, err2 = await _post(config, http, url, headers, body)
        if err2 is not None:
            logger.warning(f"Continuation failed: {err2}")
        else:
            content2, finish_reason2, usage2 = _extract(data2)
            if content2.strip():
                content += content2
                continuations = 1
                finish_reason = finish_reason2
                for key in usage:
                    usage[key] += usage2.get(key, 0)

    content = content.strip()
    if not content:
        return {
            "success": "false",
            "error": f"OpenAI returned empty content (finish_reason={finish_reason})",
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
