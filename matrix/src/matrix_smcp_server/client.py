"""Matrix client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

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

    async def _get_sync_token(self) -> str:
        """Get a sync token for pagination, doing a lightweight sync if needed."""
        if not self.sync_token:
            filter_dict = {"room": {"timeline": {"limit": 1}}}
            resp = await self.nio.sync(timeout=0, sync_filter=filter_dict)
            if isinstance(resp, SyncResponse):
                self.sync_token = resp.next_batch
            else:
                logger.error(f"Sync failed: {getattr(resp, 'message', str(resp))}")
        return self.sync_token

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
            token = await self._get_sync_token()
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

    async def list_rooms(self) -> Dict[str, Any]:
        """List joined rooms."""
        try:
            await self._get_sync_token()
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

    async def close(self):
        """Close the client session."""
        await self.nio.close()
