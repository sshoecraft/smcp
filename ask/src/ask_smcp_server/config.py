"""Configuration for the Ask SMCP server."""

from dataclasses import dataclass
from typing import Dict, Optional

from ask_smcp_server.clients import DEFAULT_MODELS, SUPPORTED_TYPES


DEFAULT_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
}

DEFAULT_SYSTEM = "You are a helpful AI assistant."
DEFAULT_MAX_TOKENS = 65536


@dataclass
class AskConfig:
    """Resolved configuration for one running ask-smcp-server instance."""
    type: str
    api_key: str
    model: str
    base_url: str
    max_tokens: int
    system: str

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "AskConfig":
        """Build an AskConfig from an SMCP credential dict (or env-var snapshot)."""
        type_value = creds.get("ASK_TYPE", "").strip().lower()
        if not type_value:
            raise ValueError("ASK_TYPE is required (one of: " + ", ".join(SUPPORTED_TYPES) + ")")
        if type_value not in SUPPORTED_TYPES:
            raise ValueError(
                f"ASK_TYPE='{type_value}' is not supported. Valid types: "
                + ", ".join(SUPPORTED_TYPES)
            )

        api_key = creds.get("ASK_API_KEY", "").strip()
        if not api_key:
            raise ValueError("ASK_API_KEY is required")

        model = creds.get("ASK_MODEL", "").strip() or DEFAULT_MODELS[type_value]
        base_url = creds.get("ASK_BASE_URL", "").strip() or DEFAULT_BASE_URLS[type_value]
        base_url = base_url.rstrip("/")

        max_tokens_raw = creds.get("ASK_MAX_TOKENS", "").strip()
        max_tokens = int(max_tokens_raw) if max_tokens_raw else DEFAULT_MAX_TOKENS

        system = creds.get("ASK_SYSTEM", "").strip() or DEFAULT_SYSTEM

        return cls(
            type=type_value,
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            system=system,
        )
