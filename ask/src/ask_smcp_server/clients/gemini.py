"""Google Gemini client."""

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
    url = f"{config.base_url}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": config.api_key,
        "Content-Type": "application/json",
    }
    body = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]},
        ],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    try:
        response = await http.post(url, headers=headers, json=body)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {"success": "false", "error": http_error_text(exc), "model": model}
    except httpx.HTTPError as exc:
        return {"success": "false", "error": str(exc), "model": model}

    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        return {"success": "false", "error": f"Gemini returned no candidates: {data}", "model": model}

    parts = candidates[0].get("content", {}).get("parts") or []
    text_chunks = [p.get("text", "") for p in parts if "text" in p]
    content = "".join(text_chunks).strip()
    if not content:
        finish = candidates[0].get("finishReason", "UNKNOWN")
        return {"success": "false", "error": f"Gemini returned empty text (finishReason={finish})", "model": model}

    return {"success": "true", "content": content, "model": model}
