"""SharePoint list MCP tools."""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_list_tools(mcp):
    """Register SharePoint list MCP tools."""

    @mcp.tool(
        name="list_lists",
        description="List SharePoint lists in a site. Uses the configured default site if site_id is empty."
    )
    async def list_lists(site_id: str = "") -> Dict[str, str]:
        """List SharePoint lists."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            lists = await mcp.client.list_lists(sid)
            results = [
                {
                    "id": l.get("id", ""),
                    "name": l.get("name", ""),
                    "displayName": l.get("displayName", ""),
                    "webUrl": l.get("webUrl", ""),
                    "list_template": l.get("list", {}).get("template", ""),
                }
                for l in lists
            ]
            return {
                "success": "true",
                "lists": json.dumps(results),
                "count": str(len(results)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing lists: {e}")
            return {
                "success": "false",
                "lists": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="get_list",
        description="Get details of a specific SharePoint list by ID. Uses the configured default site if site_id is empty."
    )
    async def get_list(list_id: str, site_id: str = "") -> Dict[str, str]:
        """Get list details."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            sp_list = await mcp.client.get_list(sid, list_id)
            if sp_list:
                return {
                    "success": "true",
                    "list": json.dumps(sp_list),
                    "error": "",
                }
            return {
                "success": "false",
                "list": "{}",
                "error": "List not found",
            }
        except Exception as e:
            logger.error(f"Error getting list {list_id}: {e}")
            return {
                "success": "false",
                "list": "{}",
                "error": str(e),
            }

    @mcp.tool(
        name="list_list_items",
        description="Get items from a SharePoint list with their field values. Uses the configured default site if site_id is empty."
    )
    async def list_list_items(
        list_id: str, site_id: str = "", expand_fields: bool = True
    ) -> Dict[str, str]:
        """List items in a SharePoint list."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            items = await mcp.client.list_list_items(sid, list_id, expand_fields)
            return {
                "success": "true",
                "items": json.dumps(items),
                "count": str(len(items)),
                "error": "",
            }
        except Exception as e:
            logger.error(f"Error listing items in list {list_id}: {e}")
            return {
                "success": "false",
                "items": "[]",
                "count": "0",
                "error": str(e),
            }

    @mcp.tool(
        name="get_list_item",
        description="Get a specific item from a SharePoint list by its ID. Uses the configured default site if site_id is empty."
    )
    async def get_list_item(
        list_id: str, item_id: str, site_id: str = ""
    ) -> Dict[str, str]:
        """Get a specific list item."""
        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            item = await mcp.client.get_list_item(sid, list_id, item_id)
            if item:
                return {
                    "success": "true",
                    "item": json.dumps(item),
                    "error": "",
                }
            return {
                "success": "false",
                "item": "{}",
                "error": "Item not found",
            }
        except Exception as e:
            logger.error(f"Error getting list item {item_id}: {e}")
            return {
                "success": "false",
                "item": "{}",
                "error": str(e),
            }

    @mcp.tool(
        name="create_list_item",
        description="Create a new item in a SharePoint list. Pass field values as a JSON string (e.g. '{\"Title\": \"New Item\"}')."
    )
    async def create_list_item(
        list_id: str, fields_json: str, site_id: str = ""
    ) -> Dict[str, str]:
        """Create a new list item."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "error": "Cannot create list item in read-only mode",
            }

        try:
            fields = json.loads(fields_json)
            sid = mcp.client._resolve_site_id(site_id or None)
            item = await mcp.client.create_list_item(sid, list_id, fields)
            if item:
                return {
                    "success": "true",
                    "item": json.dumps(item),
                    "error": "",
                }
            return {
                "success": "false",
                "item": "{}",
                "error": "Failed to create item",
            }
        except json.JSONDecodeError as e:
            return {
                "success": "false",
                "item": "{}",
                "error": f"Invalid JSON: {e}",
            }
        except Exception as e:
            logger.error(f"Error creating list item: {e}")
            return {
                "success": "false",
                "item": "{}",
                "error": str(e),
            }

    @mcp.tool(
        name="update_list_item",
        description="Update fields of an item in a SharePoint list. Pass updated fields as a JSON string."
    )
    async def update_list_item(
        list_id: str, item_id: str, fields_json: str, site_id: str = ""
    ) -> Dict[str, str]:
        """Update a list item."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "error": "Cannot update list item in read-only mode",
            }

        try:
            fields = json.loads(fields_json)
            sid = mcp.client._resolve_site_id(site_id or None)
            result = await mcp.client.update_list_item(sid, list_id, item_id, fields)
            if result:
                return {
                    "success": "true",
                    "item_id": item_id,
                    "fields": json.dumps(result),
                    "error": "",
                }
            return {
                "success": "false",
                "item_id": item_id,
                "error": "Failed to update item",
            }
        except json.JSONDecodeError as e:
            return {
                "success": "false",
                "item_id": item_id,
                "error": f"Invalid JSON: {e}",
            }
        except Exception as e:
            logger.error(f"Error updating list item {item_id}: {e}")
            return {
                "success": "false",
                "item_id": item_id,
                "error": str(e),
            }

    @mcp.tool(
        name="delete_list_item",
        description="Delete an item from a SharePoint list. Uses the configured default site if site_id is empty."
    )
    async def delete_list_item(
        list_id: str, item_id: str, site_id: str = ""
    ) -> Dict[str, str]:
        """Delete a list item."""
        if mcp.client.read_only:
            return {
                "success": "false",
                "item_id": item_id,
                "error": "Cannot delete list item in read-only mode",
            }

        try:
            sid = mcp.client._resolve_site_id(site_id or None)
            success = await mcp.client.delete_list_item(sid, list_id, item_id)
            return {
                "success": "true" if success else "false",
                "item_id": item_id,
                "error": "" if success else "Failed to delete item",
            }
        except Exception as e:
            logger.error(f"Error deleting list item {item_id}: {e}")
            return {
                "success": "false",
                "item_id": item_id,
                "error": str(e),
            }
