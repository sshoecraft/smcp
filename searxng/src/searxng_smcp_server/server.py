"""Search SMCP Server - web search via a local SearXNG instance."""

import json
import logging
import sys
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from smcp import handshake as smcp_handshake, check_credentials_schema

from searxng_smcp_server.client import SearxngClient, SearxngError, trim_results
from searxng_smcp_server.config import SearchConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s - %(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = {
    "required": {},
    "optional": {
        "SEARCH_HOST": "SearXNG hostname, IP, or full base URL (default: localhost; e.g. 192.168.1.10 or http://searx.lan:8080)",
        "SEARCH_PORT": "SearXNG port (default: 8888, ignored if SEARCH_HOST is a full URL)",
        "SEARCH_SSL": "Use HTTPS (true/false, default: false, ignored if SEARCH_HOST is a full URL)",
        "SEARCH_PATH": "Path prefix if SearXNG is mounted under a subpath (e.g. 'searx')",
        "SEARCH_USERNAME": "Basic-auth username if the instance is protected",
        "SEARCH_PASSWORD": "Basic-auth password if the instance is protected",
        "SEARCH_TIMEOUT": "HTTP request timeout in seconds (default: 30)",
        "SEARCH_LANGUAGE": "Default search language code (default: en)",
        "SEARCH_SAFESEARCH": "Default safesearch level: 0 off, 1 moderate, 2 strict (default: 0)",
        "SEARCH_MAX_RESULTS": "Default cap on results returned per call (default: 10)",
        "LOG_LEVEL": "Logging level (default: INFO)",
    },
}


def create_server(config: SearchConfig, client: SearxngClient) -> FastMCP:
    mcp = FastMCP("SearxngSMCP")

    @mcp.tool(
        name="search",
        description=(
            f"Run a web search against the SearXNG instance at {config.base_url}. "
            "Returns a JSON object with title/url/content snippets, infoboxes, "
            "suggestions, and answers."
        ),
    )
    async def search(
        query: str,
        categories: Optional[str] = None,
        engines: Optional[str] = None,
        language: Optional[str] = None,
        pageno: int = 1,
        time_range: Optional[str] = None,
        safesearch: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, str]:
        """Search the web via SearXNG.

        Args:
            query: Search query string.
            categories: Comma-separated SearXNG categories (e.g. 'general', 'news', 'images', 'it').
            engines: Comma-separated engine names to restrict the search (e.g. 'google,bing,duckduckgo').
            language: Language code override (default: configured SEARCH_LANGUAGE).
            pageno: 1-indexed result page number.
            time_range: One of 'day', 'week', 'month', 'year'.
            safesearch: 0 off, 1 moderate, 2 strict.
            max_results: Cap on number of results returned (default: configured SEARCH_MAX_RESULTS).
        """
        if not query or not query.strip():
            return {"success": "false", "error": "query is required"}

        try:
            raw = await client.search(
                query=query,
                categories=categories,
                engines=engines,
                language=language,
                pageno=pageno,
                time_range=time_range,
                safesearch=safesearch,
            )
        except SearxngError as exc:
            return {"success": "false", "error": str(exc)}
        except httpx.HTTPError as exc:
            return {"success": "false", "error": f"HTTP error contacting SearXNG: {exc}"}

        cap = max_results if max_results is not None else config.max_results
        trimmed = trim_results(raw, cap)
        return {"success": "true", "data": json.dumps(trimmed)}

    @mcp.tool(
        name="list_engines",
        description="List the search engines configured on this SearXNG instance, with their categories and enabled state.",
    )
    async def list_engines() -> Dict[str, str]:
        try:
            cfg = await client.fetch_config()
        except SearxngError as exc:
            return {"success": "false", "error": str(exc)}
        except httpx.HTTPError as exc:
            return {"success": "false", "error": f"HTTP error contacting SearXNG: {exc}"}

        engines = []
        for eng in cfg.get("engines") or []:
            engines.append({
                "name": eng.get("name"),
                "categories": eng.get("categories"),
                "enabled": not eng.get("disabled", False),
                "shortcut": eng.get("shortcut"),
                "timeout": eng.get("timeout"),
            })
        return {
            "success": "true",
            "count": str(len(engines)),
            "engines": json.dumps(engines),
        }

    return mcp


def main():
    """Main entry point for the Search SMCP service."""
    check_credentials_schema(CREDENTIALS_SCHEMA)

    try:
        creds = smcp_handshake()

        log_level = creds.get("LOG_LEVEL", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

        config = SearchConfig.from_smcp_creds(creds)
        logger.info(f"Search SMCP service starting: base_url={config.base_url}")

        http = httpx.AsyncClient(timeout=config.timeout)
        client = SearxngClient(config, http)
        mcp = create_server(config, client)
        mcp.run(transport="stdio")

    except ValueError as exc:
        logger.error(f"Configuration error: {exc}")
        sys.exit(2)
    except Exception as exc:
        logger.error(f"Error starting Search SMCP service: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
