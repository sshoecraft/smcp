"""Configuration for the Search SMCP server (SearXNG)."""

from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8888
DEFAULT_TIMEOUT = 30.0
DEFAULT_LANGUAGE = "en"
DEFAULT_SAFESEARCH = 0
DEFAULT_MAX_RESULTS = 10


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class SearchConfig:
    """Resolved configuration for one running search-smcp-server instance."""
    base_url: str
    timeout: float
    language: str
    safesearch: int
    max_results: int
    username: Optional[str]
    password: Optional[str]

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "SearchConfig":
        host = creds.get("SEARCH_HOST", "").strip() or DEFAULT_HOST

        # If the user gave a full URL, honor it verbatim; otherwise compose one.
        parsed = urlparse(host)
        if parsed.scheme and parsed.netloc:
            base_url = host.rstrip("/")
        else:
            ssl = parse_bool(creds.get("SEARCH_SSL", ""), default=False)
            scheme = "https" if ssl else "http"

            port_raw = creds.get("SEARCH_PORT", "").strip()
            port = int(port_raw) if port_raw else DEFAULT_PORT

            path = creds.get("SEARCH_PATH", "").strip().strip("/")
            base = f"{scheme}://{host}:{port}"
            if path:
                base = f"{base}/{path}"
            base_url = base.rstrip("/")

        timeout_raw = creds.get("SEARCH_TIMEOUT", "").strip()
        timeout = float(timeout_raw) if timeout_raw else DEFAULT_TIMEOUT

        language = creds.get("SEARCH_LANGUAGE", "").strip() or DEFAULT_LANGUAGE

        safesearch_raw = creds.get("SEARCH_SAFESEARCH", "").strip()
        safesearch = int(safesearch_raw) if safesearch_raw else DEFAULT_SAFESEARCH
        if safesearch not in (0, 1, 2):
            raise ValueError("SEARCH_SAFESEARCH must be 0 (off), 1 (moderate), or 2 (strict)")

        max_results_raw = creds.get("SEARCH_MAX_RESULTS", "").strip()
        max_results = int(max_results_raw) if max_results_raw else DEFAULT_MAX_RESULTS

        username = creds.get("SEARCH_USERNAME", "").strip() or None
        password = creds.get("SEARCH_PASSWORD", "") or None

        return cls(
            base_url=base_url,
            timeout=timeout,
            language=language,
            safesearch=safesearch,
            max_results=max_results,
            username=username,
            password=password,
        )
