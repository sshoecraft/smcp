"""Vendor client dispatch for the Ask SMCP server."""

from typing import Any, Dict

import httpx

SUPPORTED_TYPES = ("gemini", "openai", "anthropic")

DEFAULT_MODELS = {
    "gemini": "gemini-3.1-flash-lite",
    "openai": "gpt-5.4-nano",
    "anthropic": "claude-haiku-4-5",
}

VENDOR_DISPLAY = {
    "gemini": "Google Gemini",
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
}


async def ask(
    config,
    http: httpx.AsyncClient,
    prompt: str,
    system: str,
    model: str,
    max_tokens: int,
) -> Dict[str, Any]:
    """Dispatch a single prompt to the configured vendor and return its reply."""
    if config.type == "gemini":
        from ask_smcp_server.clients import gemini
        return await gemini.ask(config, http, prompt, system, model, max_tokens)
    if config.type == "openai":
        from ask_smcp_server.clients import openai
        return await openai.ask(config, http, prompt, system, model, max_tokens)
    if config.type == "anthropic":
        from ask_smcp_server.clients import anthropic
        return await anthropic.ask(config, http, prompt, system, model, max_tokens)
    raise ValueError(f"Unsupported type: {config.type}")
