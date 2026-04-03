"""Matrix client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from urllib.parse import quote

import aiohttp
from nio import (
    AsyncClient,
    WhoamiResponse,
    RoomSendResponse,
    JoinedRoomsResponse,
    RoomMessagesResponse,
    JoinResponse,
    RoomLeaveResponse,
    RoomCreateResponse,
    RoomInviteResponse,
    JoinedMembersResponse,
    ProfileGetResponse,
    ProfileSetDisplayNameResponse,
    RoomRedactResponse,
    RoomPutStateResponse,
    RoomGetStateResponse,
    SyncResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class MatrixConfig:
    """Configuration for Matrix client."""
    homeserver: str
    access_token: str
    user_id: str = ""

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "MatrixConfig":
        """Create config from SMCP credentials."""
        homeserver = creds.get("MATRIX_HOMESERVER")
        if not homeserver:
            raise ValueError("MATRIX_HOMESERVER credential is required")

        access_token = creds.get("MATRIX_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("MATRIX_ACCESS_TOKEN credential is required")

        return cls(
            homeserver=homeserver,
            access_token=access_token,
            user_id=creds.get("MATRIX_USER_ID", ""),
        )


class MatrixClient:
    """Matrix client wrapper for MCP tools."""

    def __init__(self, config: MatrixConfig):
        self.config = config
        self.nio = AsyncClient(config.homeserver, config.user_id or "")
        self.nio.access_token = config.access_token
        self.sync_token = ""

    # ── Helpers ──────────────────────────────────────────────────────

    async def get_sync_token(self) -> str:
        """Get a sync token for pagination, doing a lightweight sync if needed."""
        if not self.sync_token:
            filter_dict = {"room": {"timeline": {"limit": 1}}}
            resp = await self.nio.sync(timeout=0, sync_filter=filter_dict)
            if isinstance(resp, SyncResponse):
                self.sync_token = resp.next_batch
            else:
                logger.error(f"Sync failed: {getattr(resp, 'message', str(resp))}")
        return self.sync_token

    async def admin_request(self, method: str, path: str,
                             body: Optional[Dict] = None,
                             params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Synapse Admin API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /_synapse/admin/v1/rooms)
            body: Optional JSON body
            params: Optional query parameters
        """
        base = self.config.homeserver.rstrip("/")
        url = f"{base}{path}"
        headers = {
            "Authorization": f"Bearer {self.nio.access_token}",
            "Content-Type": "application/json",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers,
                                           json=body, params=params) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    else:
                        text = await resp.text()
                        return {"error": f"HTTP {resp.status}: {text}"}
        except Exception as e:
            return {"error": str(e)}

    # ── Client API: Connection ──────────────────────────────────────

    async def verify_connection(self) -> Dict[str, Any]:
        """Verify the connection and access token are valid."""
        try:
            resp = await self.nio.whoami()
            if isinstance(resp, WhoamiResponse):
                if not self.config.user_id:
                    self.config.user_id = resp.user_id
                    self.nio.user_id = resp.user_id
                return {"user_id": resp.user_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    # ── Client API: Messaging ───────────────────────────────────────

    async def send_message(self, room_id: str, body: str, html: str = "") -> Dict[str, Any]:
        """Send a text message to a room."""
        try:
            if html:
                content = {
                    "msgtype": "m.text",
                    "body": body,
                    "format": "org.matrix.custom.html",
                    "formatted_body": html,
                }
            else:
                content = {
                    "msgtype": "m.text",
                    "body": body,
                }

            resp = await self.nio.room_send(room_id, "m.room.message", content)
            if isinstance(resp, RoomSendResponse):
                return {"event_id": resp.event_id, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def read_messages(self, room_id: str, limit: int = 20) -> Dict[str, Any]:
        """Read recent messages from a room."""
        try:
            token = await self.get_sync_token()
            if not token:
                return {"error": "Failed to obtain sync token for pagination"}

            resp = await self.nio.room_messages(room_id, start=token, limit=limit)
            if isinstance(resp, RoomMessagesResponse):
                messages = []
                for event in resp.chunk:
                    msg = {
                        "sender": event.sender,
                        "event_id": event.event_id,
                        "timestamp": str(event.server_timestamp),
                    }
                    if hasattr(event, "body"):
                        msg["body"] = event.body
                        msg["type"] = getattr(event, "msgtype", "m.text")
                    elif hasattr(event, "source"):
                        content = event.source.get("content", {})
                        msg["body"] = content.get("body", "")
                        msg["type"] = content.get("msgtype", event.source.get("type", ""))
                    messages.append(msg)
                return {"messages": messages, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def send_reaction(self, room_id: str, event_id: str, reaction: str) -> Dict[str, Any]:
        """Send a reaction to a message."""
        try:
            content = {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": event_id,
                    "key": reaction,
                }
            }
            resp = await self.nio.room_send(room_id, "m.reaction", content)
            if isinstance(resp, RoomSendResponse):
                return {"event_id": resp.event_id, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def redact_message(self, room_id: str, event_id: str, reason: str = "") -> Dict[str, Any]:
        """Redact (delete) a message."""
        try:
            resp = await self.nio.room_redact(room_id, event_id, reason=reason)
            if isinstance(resp, RoomRedactResponse):
                return {"event_id": resp.event_id, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    # ── Client API: Rooms ───────────────────────────────────────────

    async def list_rooms(self) -> Dict[str, Any]:
        """List joined rooms."""
        try:
            await self.get_sync_token()
            resp = await self.nio.joined_rooms()
            if isinstance(resp, JoinedRoomsResponse):
                rooms = []
                for room_id in resp.rooms:
                    room_info = {"room_id": room_id}
                    room = self.nio.rooms.get(room_id)
                    if room:
                        room_info["name"] = room.display_name or ""
                        room_info["topic"] = room.topic or ""
                        room_info["member_count"] = str(room.member_count)
                    rooms.append(room_info)
                return {"rooms": rooms}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def join_room(self, room_id: str) -> Dict[str, Any]:
        """Join a room by ID or alias."""
        try:
            resp = await self.nio.join(room_id)
            if isinstance(resp, JoinResponse):
                return {"room_id": resp.room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def leave_room(self, room_id: str) -> Dict[str, Any]:
        """Leave a room."""
        try:
            resp = await self.nio.room_leave(room_id)
            if isinstance(resp, RoomLeaveResponse):
                return {"room_id": room_id, "status": "left"}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def create_room(self, name: str = "", topic: str = "",
                          invite: Optional[List[str]] = None,
                          is_direct: bool = False, public: bool = False) -> Dict[str, Any]:
        """Create a new room."""
        try:
            visibility = "public" if public else "private"
            resp = await self.nio.room_create(
                name=name or None,
                topic=topic or None,
                invite=invite or [],
                is_direct=is_direct,
                visibility=visibility,
            )
            if isinstance(resp, RoomCreateResponse):
                return {"room_id": resp.room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def set_room_topic(self, room_id: str, topic: str) -> Dict[str, Any]:
        """Set the topic of a room."""
        try:
            resp = await self.nio.room_put_state(
                room_id, "m.room.topic", {"topic": topic}
            )
            if isinstance(resp, RoomPutStateResponse):
                return {"event_id": resp.event_id, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def get_room_state(self, room_id: str) -> Dict[str, Any]:
        """Get the state of a room (name, topic, join rules, etc.)."""
        try:
            resp = await self.nio.room_get_state(room_id)
            if isinstance(resp, RoomGetStateResponse):
                state = {"room_id": room_id}
                for event in resp.events:
                    source = event.source if hasattr(event, "source") else event
                    event_type = source.get("type", "")
                    content = source.get("content", {})
                    if event_type == "m.room.name":
                        state["name"] = content.get("name", "")
                    elif event_type == "m.room.topic":
                        state["topic"] = content.get("topic", "")
                    elif event_type == "m.room.canonical_alias":
                        state["alias"] = content.get("alias", "")
                    elif event_type == "m.room.create":
                        state["creator"] = content.get("creator", "")
                    elif event_type == "m.room.join_rules":
                        state["join_rule"] = content.get("join_rule", "")
                    elif event_type == "m.room.guest_access":
                        state["guest_access"] = content.get("guest_access", "")
                    elif event_type == "m.room.history_visibility":
                        state["history_visibility"] = content.get("history_visibility", "")
                return state
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    # ── Client API: Users ───────────────────────────────────────────

    async def invite_user(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """Invite a user to a room."""
        try:
            resp = await self.nio.room_invite(room_id, user_id)
            if isinstance(resp, RoomInviteResponse):
                return {"room_id": room_id, "user_id": user_id, "status": "invited"}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def get_room_members(self, room_id: str) -> Dict[str, Any]:
        """Get members of a room."""
        try:
            resp = await self.nio.joined_members(room_id)
            if isinstance(resp, JoinedMembersResponse):
                members = []
                for member in resp.members:
                    members.append({
                        "user_id": member.user_id,
                        "display_name": member.display_name or "",
                        "avatar_url": member.avatar_url or "",
                    })
                return {"members": members, "room_id": room_id}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get a user's profile."""
        try:
            resp = await self.nio.get_profile(user_id)
            if isinstance(resp, ProfileGetResponse):
                return {
                    "user_id": user_id,
                    "display_name": resp.displayname or "",
                    "avatar_url": resp.avatar_url or "",
                }
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    async def set_display_name(self, display_name: str) -> Dict[str, Any]:
        """Set the display name for the authenticated user."""
        try:
            resp = await self.nio.set_displayname(display_name)
            if isinstance(resp, ProfileSetDisplayNameResponse):
                return {"display_name": display_name, "status": "updated"}
            return {"error": getattr(resp, "message", str(resp))}
        except Exception as e:
            return {"error": str(e)}

    # ── Admin API: Rooms ────────────────────────────────────────────

    async def destroy_room(self, room_id: str, block: bool = False,
                           purge: bool = True, force_purge: bool = False) -> Dict[str, Any]:
        """Destroy a room via Synapse Admin API."""
        body = {"block": block, "purge": purge, "force_purge": force_purge}
        result = await self.admin_request("DELETE", f"/_synapse/admin/v2/rooms/{room_id}", body=body)
        if "error" in result:
            return result
        return {"delete_id": result.get("delete_id", ""), "room_id": room_id}

    async def list_all_rooms(self, order_by: str = "name", direction: str = "f",
                             search_term: str = "", limit: int = 100,
                             offset: int = 0) -> Dict[str, Any]:
        """List all rooms on the server via Synapse Admin API."""
        params = {"order_by": order_by, "dir": direction, "limit": str(limit), "from": str(offset)}
        if search_term:
            params["search_term"] = search_term
        return await self.admin_request("GET", "/_synapse/admin/v1/rooms", params=params)

    async def get_room_details(self, room_id: str) -> Dict[str, Any]:
        """Get detailed room info via Synapse Admin API."""
        return await self.admin_request("GET", f"/_synapse/admin/v1/rooms/{room_id}")

    async def block_room(self, room_id: str, block: bool = True) -> Dict[str, Any]:
        """Block or unblock a room via Synapse Admin API."""
        return await self.admin_request("PUT", f"/_synapse/admin/v1/rooms/{room_id}/block",
                                         body={"block": block})

    async def make_room_admin(self, room_id: str, user_id: str = "") -> Dict[str, Any]:
        """Grant a user admin privileges in a room via Synapse Admin API."""
        body = {}
        if user_id:
            body["user_id"] = user_id
        return await self.admin_request("POST", f"/_synapse/admin/v1/rooms/{room_id}/make_room_admin",
                                         body=body)

    async def purge_history(self, room_id: str, purge_up_to_ts: int) -> Dict[str, Any]:
        """Purge room history up to a timestamp via Synapse Admin API."""
        body = {"purge_up_to_ts": purge_up_to_ts}
        return await self.admin_request("POST", f"/_synapse/admin/v1/purge_history/{room_id}",
                                         body=body)

    # ── Admin API: Users ────────────────────────────────────────────

    async def get_user_admin(self, user_id: str) -> Dict[str, Any]:
        """Get user account info via Synapse Admin API."""
        return await self.admin_request("GET", f"/_synapse/admin/v2/users/{quote(user_id, safe='')}")

    async def modify_user(self, user_id: str, displayname: str = "", admin: Optional[bool] = None,
                          deactivated: Optional[bool] = None, password: str = "",
                          avatar_url: str = "", threepids: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Modify a user account via Synapse Admin API."""
        body: Dict[str, Any] = {}
        if displayname:
            body["displayname"] = displayname
        if admin is not None:
            body["admin"] = admin
        if deactivated is not None:
            body["deactivated"] = deactivated
        if password:
            body["password"] = password
        if avatar_url:
            body["avatar_url"] = avatar_url
        if threepids is not None:
            body["threepids"] = threepids
        return await self.admin_request("PUT", f"/_synapse/admin/v2/users/{quote(user_id, safe='')}",
                                         body=body)

    async def deactivate_user(self, user_id: str, erase: bool = False) -> Dict[str, Any]:
        """Deactivate a user account via Synapse Admin API."""
        body = {"erase": erase}
        return await self.admin_request("POST", f"/_synapse/admin/v1/deactivate/{quote(user_id, safe='')}",
                                         body=body)

    async def reset_password(self, user_id: str, new_password: str,
                             logout_devices: bool = True) -> Dict[str, Any]:
        """Reset a user's password via Synapse Admin API."""
        body = {"new_password": new_password, "logout_devices": logout_devices}
        return await self.admin_request("POST",
                                         f"/_synapse/admin/v1/reset_password/{quote(user_id, safe='')}",
                                         body=body)

    async def whois_user(self, user_id: str) -> Dict[str, Any]:
        """Get active sessions for a user via Synapse Admin API."""
        return await self.admin_request("GET", f"/_synapse/admin/v1/whois/{quote(user_id, safe='')}")

    async def list_user_devices(self, user_id: str) -> Dict[str, Any]:
        """List all devices for a user via Synapse Admin API."""
        return await self.admin_request("GET",
                                         f"/_synapse/admin/v2/users/{quote(user_id, safe='')}/devices")

    async def delete_user_device(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Delete a specific device for a user via Synapse Admin API."""
        return await self.admin_request("DELETE",
                                         f"/_synapse/admin/v2/users/{quote(user_id, safe='')}/devices/{device_id}")

    # ── Admin API: Server ───────────────────────────────────────────

    async def get_server_version(self) -> Dict[str, Any]:
        """Get Synapse server version via Admin API."""
        return await self.admin_request("GET", "/_synapse/admin/v1/server_version")

    async def list_event_reports(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List event reports via Synapse Admin API."""
        params = {"limit": str(limit), "from": str(offset)}
        return await self.admin_request("GET", "/_synapse/admin/v1/event_reports", params=params)

    async def get_user_media_stats(self, order_by: str = "media_length",
                                   direction: str = "b", search_term: str = "",
                                   limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get per-user media usage statistics via Synapse Admin API."""
        params = {"order_by": order_by, "dir": direction,
                  "limit": str(limit), "from": str(offset)}
        if search_term:
            params["search_term"] = search_term
        return await self.admin_request("GET", "/_synapse/admin/v1/statistics/users/media",
                                         params=params)

    # ── Admin API: Registration Tokens ──────────────────────────────

    async def create_registration_token(self, token: str = "",
                                        uses_allowed: Optional[int] = None,
                                        expiry_time: Optional[int] = None) -> Dict[str, Any]:
        """Create a registration token via Synapse Admin API."""
        body: Dict[str, Any] = {}
        if token:
            body["token"] = token
        if uses_allowed is not None:
            body["uses_allowed"] = uses_allowed
        if expiry_time is not None:
            body["expiry_time"] = expiry_time
        return await self.admin_request("POST", "/_synapse/admin/v1/registration_tokens/new",
                                         body=body)

    async def list_registration_tokens(self, valid: Optional[bool] = None) -> Dict[str, Any]:
        """List registration tokens via Synapse Admin API."""
        params = {}
        if valid is not None:
            params["valid"] = "true" if valid else "false"
        return await self.admin_request("GET", "/_synapse/admin/v1/registration_tokens",
                                         params=params)

    async def revoke_registration_token(self, token: str) -> Dict[str, Any]:
        """Delete a registration token via Synapse Admin API."""
        return await self.admin_request("DELETE",
                                         f"/_synapse/admin/v1/registration_tokens/{token}")

    # ── Admin API: Media ────────────────────────────────────────────

    async def delete_media(self, server_name: str, media_id: str) -> Dict[str, Any]:
        """Delete a specific media item via Synapse Admin API."""
        return await self.admin_request("DELETE",
                                         f"/_synapse/admin/v1/media/{server_name}/{media_id}")

    async def purge_media_cache(self, before_ts: int) -> Dict[str, Any]:
        """Purge cached remote media older than timestamp via Synapse Admin API."""
        params = {"before_ts": str(before_ts)}
        return await self.admin_request("POST", "/_synapse/admin/v1/purge_media_cache",
                                         params=params)

    # ── Lifecycle ───────────────────────────────────────────────────

    async def close(self):
        """Close the client session."""
        await self.nio.close()
