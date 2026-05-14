"""Shared helpers for vendor clients."""

import httpx


def http_error_text(exc: httpx.HTTPStatusError) -> str:
    """Return a compact, readable error from an HTTP status error."""
    response = exc.response
    body = response.text
    if len(body) > 800:
        body = body[:800] + "...(truncated)"
    return f"HTTP {response.status_code}: {body}"
