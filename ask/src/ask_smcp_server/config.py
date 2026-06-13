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
DEFAULT_TIMEOUT = 600.0
DEFAULT_THINKING_LEVEL = "high"
DEFAULT_AUTO_CONTINUE = True
DEFAULT_REASONING_EFFORT = None

VALID_THINKING_LEVELS = ("minimal", "low", "medium", "high")
VALID_REASONING_EFFORTS = ("minimal", "low", "medium", "high")


@dataclass
class AskConfig:
    """Resolved configuration for one running ask-smcp-server instance."""
    type: str
    api_key: str
    model: str
    base_url: str
    max_tokens: int
    system: str
    timeout: float
    thinking_level: str
    auto_continue: bool
    reasoning_effort: Optional[str]

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

        timeout_raw = creds.get("ASK_TIMEOUT", "").strip()
        timeout = float(timeout_raw) if timeout_raw else DEFAULT_TIMEOUT

        thinking_level = creds.get("ASK_THINKING_LEVEL", "").strip().lower() or DEFAULT_THINKING_LEVEL
        if thinking_level not in VALID_THINKING_LEVELS:
            raise ValueError(
                f"ASK_THINKING_LEVEL='{thinking_level}' is not supported. Valid values: "
                + ", ".join(VALID_THINKING_LEVELS)
            )

        auto_continue_raw = creds.get("ASK_AUTO_CONTINUE", "").strip().lower()
        if auto_continue_raw == "":
            auto_continue = DEFAULT_AUTO_CONTINUE
        else:
            auto_continue = auto_continue_raw in ("1", "true", "yes", "on")

        reasoning_effort = creds.get("ASK_REASONING_EFFORT", "").strip().lower() or DEFAULT_REASONING_EFFORT
        if reasoning_effort is not None and reasoning_effort not in VALID_REASONING_EFFORTS:
            raise ValueError(
                f"ASK_REASONING_EFFORT='{reasoning_effort}' is not supported. Valid values: "
                + ", ".join(VALID_REASONING_EFFORTS)
            )

        return cls(
            type=type_value,
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            system=system,
            timeout=timeout,
            thinking_level=thinking_level,
            auto_continue=auto_continue,
            reasoning_effort=reasoning_effort,
        )
