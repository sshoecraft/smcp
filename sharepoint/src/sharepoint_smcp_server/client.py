"""SharePoint client wrapper using Microsoft Graph API."""

import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx
from azure.identity import ClientSecretCredential, UsernamePasswordCredential

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


@dataclass
class SharePointConfig:
    """Configuration for SharePoint client."""
    tenant_id: str
    client_id: str
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    site_url: Optional[str] = None
    read_only: bool = False

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "SharePointConfig":
        """Create config from SMCP credentials."""
        tenant_id = creds.get("TENANT_ID")
        if not tenant_id:
            raise ValueError("TENANT_ID credential is required")
        client_id = creds.get("CLIENT_ID")
        if not client_id:
            raise ValueError("CLIENT_ID credential is required")

        client_secret = creds.get("CLIENT_SECRET")
        username = creds.get("USERNAME")
        password = creds.get("PASSWORD")

        if not client_secret and not (username and password):
            raise ValueError(
                "Either CLIENT_SECRET or USERNAME+PASSWORD must be provided"
            )

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            site_url=creds.get("SITE_URL"),
            read_only=creds.get("READ_ONLY_MODE", "false").lower() == "true",
        )


class SharePointClient:
    """SharePoint client using Microsoft Graph REST API."""

    def __init__(self, config: SharePointConfig):
        self._config = config
        self._read_only = config.read_only
        if config.client_secret:
            self._credential = ClientSecretCredential(
                tenant_id=config.tenant_id,
                client_id=config.client_id,
                client_secret=config.client_secret,
            )
        else:
            self._credential = UsernamePasswordCredential(
                client_id=config.client_id,
                tenant_id=config.tenant_id,
                username=config.username,
                password=config.password,
            )
        self._http = httpx.AsyncClient(timeout=60.0)
        self._token: Optional[str] = None
        self._token_expires: float = 0
        self._default_site_id: Optional[str] = None

    @property
    def read_only(self) -> bool:
        """Whether the client is in read-only mode."""
        return self._read_only

    @property
    def default_site_id(self) -> Optional[str]:
        """The default site ID resolved from SITE_URL, if configured."""
        return self._default_site_id

    async def initialize(self):
        """Resolve SITE_URL to a Graph site ID if configured."""
        if self._config.site_url:
            parsed = urlparse(self._config.site_url)
            hostname = parsed.hostname
            # Strip leading slash and trailing slash from path
            path = parsed.path.strip("/")
            if path:
                endpoint = f"/sites/{hostname}:/{path}"
            else:
                endpoint = f"/sites/{hostname}"
            site = await self._get(endpoint)
            self._default_site_id = site["id"]
            logger.info(f"Resolved SITE_URL to site ID: {self._default_site_id}")

    async def close(self):
        """Close the HTTP client."""
        await self._http.aclose()

    # ── Auth ──────────────────────────────────────────────────────────

    async def _ensure_token(self):
        """Refresh the bearer token if expired or about to expire."""
        if self._token and time.time() < self._token_expires - 60:
            return
        token = await asyncio.to_thread(
            self._credential.get_token, GRAPH_SCOPE
        )
        self._token = token.token
        self._token_expires = token.expires_on
        logger.debug("Refreshed Graph API bearer token")

    def _auth_headers(self) -> Dict[str, str]:
        """Return authorization headers."""
        return {"Authorization": f"Bearer {self._token}"}

    # ── HTTP helpers ──────────────────────────────────────────────────

    async def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET request to Graph API."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        resp = await self._http.get(url, headers=self._auth_headers(), params=params)
        return self._handle_response(resp)

    async def _get_bytes(self, path: str) -> bytes:
        """GET request that returns raw bytes (for file downloads)."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        resp = await self._http.get(url, headers=self._auth_headers(), follow_redirects=True)
        resp.raise_for_status()
        return resp.content

    async def _post(self, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request to Graph API."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        resp = await self._http.post(url, headers=self._auth_headers(), json=json_body)
        return self._handle_response(resp)

    async def _put_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """PUT request with raw bytes (for file uploads)."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        headers = {**self._auth_headers(), "Content-Type": content_type}
        resp = await self._http.put(url, headers=headers, content=data)
        return self._handle_response(resp)

    async def _patch(self, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH request to Graph API."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        resp = await self._http.patch(url, headers=self._auth_headers(), json=json_body)
        return self._handle_response(resp)

    async def _delete(self, path: str) -> bool:
        """DELETE request to Graph API. Returns True on success."""
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        resp = await self._http.delete(url, headers=self._auth_headers())
        if resp.status_code == 204:
            return True
        self._handle_response(resp)  # will raise on error
        return True

    async def _paginated_get(self, path: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """GET with automatic @odata.nextLink pagination."""
        results: List[Dict[str, Any]] = []
        await self._ensure_token()
        url = f"{GRAPH_BASE}{path}"
        while url:
            resp = await self._http.get(url, headers=self._auth_headers(), params=params)
            data = self._handle_response(resp)
            results.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            params = None  # nextLink includes params already
        return results

    def _handle_response(self, resp: httpx.Response) -> Dict[str, Any]:
        """Parse response JSON or raise on error."""
        if resp.status_code == 204:
            return {}
        try:
            body = resp.json()
        except Exception:
            resp.raise_for_status()
            return {}
        if resp.is_error:
            error = body.get("error", {})
            code = error.get("code", "UnknownError")
            message = error.get("message", resp.text)
            raise GraphAPIError(resp.status_code, code, message)
        return body

    # ── Path helpers ──────────────────────────────────────────────────

    def _resolve_site_id(self, site_id: Optional[str]) -> str:
        """Return the given site_id or fall back to the default."""
        sid = site_id or self._default_site_id
        if not sid:
            raise ValueError(
                "No site_id provided and no default site configured via SITE_URL"
            )
        return sid

    @staticmethod
    def _item_path_segment(item_path: str) -> str:
        """Build the Graph path segment for a drive item path.

        Returns either '/root' for root, or '/root:/{encoded_path}:' for subpaths.
        """
        path = item_path.strip("/")
        if not path:
            return "/root"
        encoded = quote(path, safe="/")
        return f"/root:/{encoded}:"

    # ── Sites ─────────────────────────────────────────────────────────

    async def list_sites(self) -> List[Dict[str, Any]]:
        """List all sites accessible to the app."""
        try:
            return await self._paginated_get("/sites", params={"search": "*"})
        except Exception as e:
            logger.error(f"Error listing sites: {e}")
            return []

    async def search_sites(self, query: str) -> List[Dict[str, Any]]:
        """Search for sites by keyword."""
        try:
            return await self._paginated_get("/sites", params={"search": query})
        except Exception as e:
            logger.error(f"Error searching sites: {e}")
            return []

    async def get_site(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific site."""
        try:
            return await self._get(f"/sites/{site_id}")
        except Exception as e:
            logger.error(f"Error getting site {site_id}: {e}")
            return None

    async def get_site_by_url(self, site_url: str) -> Optional[Dict[str, Any]]:
        """Get a site by its URL."""
        try:
            parsed = urlparse(site_url)
            hostname = parsed.hostname
            path = parsed.path.strip("/")
            if path:
                endpoint = f"/sites/{hostname}:/{path}"
            else:
                endpoint = f"/sites/{hostname}"
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting site by URL {site_url}: {e}")
            return None

    # ── Drives ────────────────────────────────────────────────────────

    async def list_drives(self, site_id: str) -> List[Dict[str, Any]]:
        """List document libraries (drives) in a site."""
        try:
            return await self._paginated_get(f"/sites/{site_id}/drives")
        except Exception as e:
            logger.error(f"Error listing drives for site {site_id}: {e}")
            return []

    async def get_drive(self, drive_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific drive."""
        try:
            return await self._get(f"/drives/{drive_id}")
        except Exception as e:
            logger.error(f"Error getting drive {drive_id}: {e}")
            return None

    # ── Drive Items (files/folders) ───────────────────────────────────

    async def list_children(self, drive_id: str, item_path: str = "/") -> List[Dict[str, Any]]:
        """List children (files/folders) at a path in a drive."""
        try:
            segment = self._item_path_segment(item_path)
            return await self._paginated_get(f"/drives/{drive_id}{segment}/children")
        except Exception as e:
            logger.error(f"Error listing children at {item_path}: {e}")
            return []

    async def get_item(self, drive_id: str, item_path: str) -> Optional[Dict[str, Any]]:
        """Get properties of a file or folder."""
        try:
            segment = self._item_path_segment(item_path)
            return await self._get(f"/drives/{drive_id}{segment}")
        except Exception as e:
            logger.error(f"Error getting item {item_path}: {e}")
            return None

    async def search_items(self, drive_id: str, query: str) -> List[Dict[str, Any]]:
        """Search for items within a drive."""
        try:
            return await self._paginated_get(
                f"/drives/{drive_id}/root/search(q='{quote(query)}')"
            )
        except Exception as e:
            logger.error(f"Error searching items in drive {drive_id}: {e}")
            return []

    async def download_item_content(self, drive_id: str, item_path: str) -> Optional[bytes]:
        """Download file content as bytes."""
        try:
            segment = self._item_path_segment(item_path)
            return await self._get_bytes(f"/drives/{drive_id}{segment}/content")
        except Exception as e:
            logger.error(f"Error downloading {item_path}: {e}")
            return None

    async def upload_item_content(self, drive_id: str, item_path: str, data: bytes) -> Optional[Dict[str, Any]]:
        """Upload content to a file (simple upload, <=4MB)."""
        try:
            segment = self._item_path_segment(item_path)
            return await self._put_bytes(
                f"/drives/{drive_id}{segment}/content",
                data=data,
            )
        except Exception as e:
            logger.error(f"Error uploading to {item_path}: {e}")
            return None

    async def create_folder(self, drive_id: str, parent_path: str, folder_name: str) -> Optional[Dict[str, Any]]:
        """Create a new folder."""
        try:
            segment = self._item_path_segment(parent_path)
            return await self._post(
                f"/drives/{drive_id}{segment}/children",
                json_body={
                    "name": folder_name,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "fail",
                },
            )
        except Exception as e:
            logger.error(f"Error creating folder {folder_name}: {e}")
            return None

    async def delete_item(self, drive_id: str, item_path: str) -> bool:
        """Delete a file or folder."""
        try:
            # Resolve path to item ID first
            item = await self.get_item(drive_id, item_path)
            if not item:
                return False
            item_id = item["id"]
            return await self._delete(f"/drives/{drive_id}/items/{item_id}")
        except Exception as e:
            logger.error(f"Error deleting {item_path}: {e}")
            return False

    async def move_item(self, drive_id: str, item_path: str,
                        new_name: Optional[str] = None,
                        destination_parent_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Move and/or rename a file or folder."""
        try:
            item = await self.get_item(drive_id, item_path)
            if not item:
                return None
            item_id = item["id"]

            body: Dict[str, Any] = {}
            if new_name:
                body["name"] = new_name
            if destination_parent_path:
                parent = await self.get_item(drive_id, destination_parent_path)
                if not parent:
                    return None
                body["parentReference"] = {"id": parent["id"]}

            if not body:
                return item  # nothing to change

            return await self._patch(f"/drives/{drive_id}/items/{item_id}", body)
        except Exception as e:
            logger.error(f"Error moving {item_path}: {e}")
            return None

    async def copy_item(self, drive_id: str, item_path: str,
                        destination_parent_path: str,
                        new_name: Optional[str] = None) -> bool:
        """Copy a file or folder. Returns True if the copy was accepted."""
        try:
            item = await self.get_item(drive_id, item_path)
            if not item:
                return False
            item_id = item["id"]

            parent = await self.get_item(drive_id, destination_parent_path)
            if not parent:
                return False

            body: Dict[str, Any] = {
                "parentReference": {"driveId": drive_id, "id": parent["id"]},
            }
            if new_name:
                body["name"] = new_name

            await self._ensure_token()
            url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/copy"
            resp = await self._http.post(url, headers=self._auth_headers(), json=body)
            # Copy returns 202 Accepted with a monitor URL
            if resp.status_code in (200, 202):
                return True
            self._handle_response(resp)
            return True
        except Exception as e:
            logger.error(f"Error copying {item_path}: {e}")
            return False

    # ── Lists ─────────────────────────────────────────────────────────

    async def list_lists(self, site_id: str) -> List[Dict[str, Any]]:
        """List SharePoint lists in a site."""
        try:
            return await self._paginated_get(f"/sites/{site_id}/lists")
        except Exception as e:
            logger.error(f"Error listing lists for site {site_id}: {e}")
            return []

    async def get_list(self, site_id: str, list_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific list."""
        try:
            return await self._get(f"/sites/{site_id}/lists/{list_id}")
        except Exception as e:
            logger.error(f"Error getting list {list_id}: {e}")
            return None

    async def list_list_items(self, site_id: str, list_id: str,
                              expand_fields: bool = True) -> List[Dict[str, Any]]:
        """Get items from a SharePoint list."""
        try:
            params = {}
            if expand_fields:
                params["expand"] = "fields"
            return await self._paginated_get(
                f"/sites/{site_id}/lists/{list_id}/items", params=params
            )
        except Exception as e:
            logger.error(f"Error listing items in list {list_id}: {e}")
            return []

    async def get_list_item(self, site_id: str, list_id: str,
                            item_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific list item."""
        try:
            return await self._get(
                f"/sites/{site_id}/lists/{list_id}/items/{item_id}",
                params={"expand": "fields"},
            )
        except Exception as e:
            logger.error(f"Error getting list item {item_id}: {e}")
            return None

    async def create_list_item(self, site_id: str, list_id: str,
                               fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new item in a SharePoint list."""
        try:
            return await self._post(
                f"/sites/{site_id}/lists/{list_id}/items",
                json_body={"fields": fields},
            )
        except Exception as e:
            logger.error(f"Error creating list item in {list_id}: {e}")
            return None

    async def update_list_item(self, site_id: str, list_id: str,
                               item_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of a list item."""
        try:
            return await self._patch(
                f"/sites/{site_id}/lists/{list_id}/items/{item_id}/fields",
                fields,
            )
        except Exception as e:
            logger.error(f"Error updating list item {item_id}: {e}")
            return None

    async def delete_list_item(self, site_id: str, list_id: str,
                               item_id: str) -> bool:
        """Delete an item from a SharePoint list."""
        try:
            return await self._delete(
                f"/sites/{site_id}/lists/{list_id}/items/{item_id}"
            )
        except Exception as e:
            logger.error(f"Error deleting list item {item_id}: {e}")
            return False

    # ── Permissions ───────────────────────────────────────────────────

    async def list_permissions(self, drive_id: str, item_path: str) -> List[Dict[str, Any]]:
        """List permissions on a drive item."""
        try:
            item = await self.get_item(drive_id, item_path)
            if not item:
                return []
            item_id = item["id"]
            return await self._paginated_get(
                f"/drives/{drive_id}/items/{item_id}/permissions"
            )
        except Exception as e:
            logger.error(f"Error listing permissions for {item_path}: {e}")
            return []

    async def create_sharing_link(self, drive_id: str, item_path: str,
                                  link_type: str = "view",
                                  scope: str = "anonymous",
                                  expiration_datetime: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a sharing link for a file or folder."""
        try:
            item = await self.get_item(drive_id, item_path)
            if not item:
                return None
            item_id = item["id"]

            body: Dict[str, Any] = {
                "type": link_type,
                "scope": scope,
            }
            if expiration_datetime:
                body["expirationDateTime"] = expiration_datetime

            return await self._post(
                f"/drives/{drive_id}/items/{item_id}/createLink",
                json_body=body,
            )
        except Exception as e:
            logger.error(f"Error creating sharing link for {item_path}: {e}")
            return None

    async def delete_permission(self, drive_id: str, item_path: str,
                                permission_id: str) -> bool:
        """Remove a permission from a drive item."""
        try:
            item = await self.get_item(drive_id, item_path)
            if not item:
                return False
            item_id = item["id"]
            return await self._delete(
                f"/drives/{drive_id}/items/{item_id}/permissions/{permission_id}"
            )
        except Exception as e:
            logger.error(f"Error deleting permission {permission_id}: {e}")
            return False


class GraphAPIError(Exception):
    """Error from Microsoft Graph API."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        super().__init__(f"Graph API error {status_code} ({code}): {message}")
