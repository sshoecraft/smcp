"""Thin HTTP client wrapping a SearXNG instance's JSON API."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from searxng_smcp_server.config import SearchConfig

logger = logging.getLogger(__name__)


class SearxngError(Exception):
    """Raised when SearXNG returns an error or unusable response."""


class SearxngClient:
    def __init__(self, config: SearchConfig, http: httpx.AsyncClient):
        self.config = config
        self.http = http

    def _auth(self):
        if self.config.username and self.config.password is not None:
            return (self.config.username, self.config.password)
        return None

    async def search(
        self,
        query: str,
        categories: Optional[str] = None,
        engines: Optional[str] = None,
        language: Optional[str] = None,
        pageno: int = 1,
        time_range: Optional[str] = None,
        safesearch: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "q": query,
            "format": "json",
            "language": language or self.config.language,
            "pageno": pageno,
            "safesearch": safesearch if safesearch is not None else self.config.safesearch,
        }
        if categories:
            params["categories"] = categories
        if engines:
            params["engines"] = engines
        if time_range:
            params["time_range"] = time_range

        url = f"{self.config.base_url}/search"
        resp = await self.http.get(url, params=params, auth=self._auth(), timeout=self.config.timeout)
        if resp.status_code != 200:
            raise SearxngError(
                f"SearXNG returned HTTP {resp.status_code}: {resp.text[:300]}"
            )

        try:
            data = resp.json()
        except Exception as exc:
            raise SearxngError(
                f"SearXNG response was not JSON (is the JSON format enabled in settings.yml?): {exc}"
            )
        return data

    async def fetch_config(self) -> Dict[str, Any]:
        url = f"{self.config.base_url}/config"
        resp = await self.http.get(url, auth=self._auth(), timeout=self.config.timeout)
        if resp.status_code != 200:
            raise SearxngError(
                f"SearXNG /config returned HTTP {resp.status_code}: {resp.text[:300]}"
            )
        return resp.json()


def trim_results(data: Dict[str, Any], max_results: int) -> Dict[str, Any]:
    """Strip the SearXNG response down to fields useful to an LLM caller."""
    results: List[Dict[str, Any]] = []
    for item in (data.get("results") or [])[:max_results]:
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
            "engine": item.get("engine"),
            "score": item.get("score"),
            "publishedDate": item.get("publishedDate"),
            "category": item.get("category"),
        })

    infoboxes = []
    for box in data.get("infoboxes") or []:
        infoboxes.append({
            "infobox": box.get("infobox"),
            "content": box.get("content"),
            "urls": box.get("urls"),
        })

    return {
        "query": data.get("query"),
        "number_of_results": data.get("number_of_results"),
        "result_count": len(results),
        "results": results,
        "infoboxes": infoboxes,
        "suggestions": data.get("suggestions") or [],
        "answers": data.get("answers") or [],
    }
