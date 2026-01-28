"""MCP tools for eBay operations."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register eBay MCP tools."""

    @mcp.tool(
        name="search",
        description="Search eBay listings with configurable filters for buying options and condition"
    )
    async def search(
        query: str,
        limit: int = 10,
        buying_options: str = "all",
        condition: str = "any"
    ) -> Dict[str, str]:
        """Search eBay listings.

        Args:
            query: Search query string
            limit: Maximum number of results (default: 10, max: 200)
            buying_options: Filter - all, fixed_price (or buy_it_now), auction, best_offer
            condition: Filter - any, new, used
        """
        try:
            results = await mcp.client.search(
                query=query,
                limit=limit,
                buying_options=buying_options,
                condition=condition
            )

            if not results:
                return {
                    "success": "true",
                    "count": "0",
                    "results": "[]"
                }

            return {
                "success": "true",
                "count": str(len(results)),
                "results": json.dumps(results, indent=2)
            }
        except Exception as e:
            logger.error(f"Error searching eBay: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool(
        name="get_item",
        description="Get detailed information for a specific eBay item including description, specifics, and shipping"
    )
    async def get_item(item_id: str) -> Dict[str, str]:
        """Get detailed item information.

        Args:
            item_id: eBay item ID (from search results)
        """
        try:
            item = await mcp.client.get_item(item_id)
            return {
                "success": "true",
                "item": json.dumps(item, indent=2)
            }
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {e}")
            return {"success": "false", "error": str(e)}
