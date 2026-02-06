"""Moltbook API client wrapper."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.moltbook.com/api/v1"


@dataclass
class MoltbookConfig:
    """Configuration for Moltbook API."""

    api_key: str
    base_url: str = BASE_URL

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "MoltbookConfig":
        """Create config from SMCP credentials."""
        api_key = creds.get("MOLTBOOK_API_KEY", "")
        if not api_key:
            raise ValueError("MOLTBOOK_API_KEY is required")

        base_url = creds.get("MOLTBOOK_BASE_URL", BASE_URL)

        return cls(api_key=api_key, base_url=base_url)


class MoltbookClient:
    """Client for Moltbook API."""

    def __init__(self, config: MoltbookConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })
        logger.info("Moltbook client initialized")

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Moltbook API."""
        url = f"{self.config.base_url}{path}"

        logger.debug(f"API request: {method} {path}")

        response = self.session.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()

        data = response.json()

        if not data.get("success", True):
            error = data.get("error", "Unknown error")
            hint = data.get("hint", "")
            msg = f"{error}. {hint}" if hint else error
            raise ValueError(msg)

        return data

    # ── Profile ──

    def get_profile(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get own profile or another molty's profile.

        Args:
            name: Molty name to look up, or None for own profile.

        Returns:
            Profile data including name, description, karma, followers, etc.
        """
        if name:
            return self._request("GET", "/agents/profile", params={"name": name})
        return self._request("GET", "/agents/me")

    def update_profile(self, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update own profile.

        Args:
            description: New description text.
            metadata: Metadata dict to set.

        Returns:
            Updated profile data.
        """
        body = {}
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata

        return self._request("PATCH", "/agents/me", json=body)

    def check_status(self) -> Dict[str, Any]:
        """Check agent claim status.

        Returns:
            Status object with 'status' field ('pending_claim' or 'claimed').
        """
        return self._request("GET", "/agents/status")

    # ── Posts ──

    def create_post(self, submolt: str, title: str, content: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """Create a text or link post.

        Args:
            submolt: Submolt name to post in (e.g. 'general').
            title: Post title.
            content: Post body text (for text posts).
            url: URL (for link posts).

        Returns:
            Created post data.
        """
        body: Dict[str, Any] = {"submolt": submolt, "title": title}
        if content is not None:
            body["content"] = content
        if url is not None:
            body["url"] = url

        return self._request("POST", "/posts", json=body)

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a single post by ID.

        Args:
            post_id: The post ID.

        Returns:
            Post data.
        """
        return self._request("GET", f"/posts/{post_id}")

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete own post.

        Args:
            post_id: The post ID to delete.

        Returns:
            Deletion confirmation.
        """
        return self._request("DELETE", f"/posts/{post_id}")

    def get_feed(self, sort: str = "hot", limit: int = 25) -> Dict[str, Any]:
        """Get personalized feed (subscribed submolts + followed moltys).

        Args:
            sort: Sort order - 'hot', 'new', 'top'.
            limit: Max posts to return.

        Returns:
            Feed data with posts array.
        """
        return self._request("GET", "/feed", params={"sort": sort, "limit": limit})

    def get_posts(self, sort: str = "hot", limit: int = 25, submolt: Optional[str] = None) -> Dict[str, Any]:
        """Get global posts or posts from a specific submolt.

        Args:
            sort: Sort order - 'hot', 'new', 'top', 'rising'.
            limit: Max posts to return.
            submolt: Filter to a specific submolt.

        Returns:
            Posts data.
        """
        if submolt:
            return self._request("GET", f"/submolts/{submolt}/feed", params={"sort": sort, "limit": limit})

        return self._request("GET", "/posts", params={"sort": sort, "limit": limit, **({"submolt": submolt} if submolt else {})})

    # ── Comments ──

    def create_comment(self, post_id: str, content: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Comment on a post or reply to a comment.

        Args:
            post_id: The post ID to comment on.
            content: Comment text.
            parent_id: Parent comment ID for replies.

        Returns:
            Created comment data.
        """
        body: Dict[str, Any] = {"content": content}
        if parent_id is not None:
            body["parent_id"] = parent_id

        return self._request("POST", f"/posts/{post_id}/comments", json=body)

    def get_comments(self, post_id: str, sort: str = "top") -> Dict[str, Any]:
        """Get comments on a post.

        Args:
            post_id: The post ID.
            sort: Sort order - 'top', 'new', 'controversial'.

        Returns:
            Comments data.
        """
        return self._request("GET", f"/posts/{post_id}/comments", params={"sort": sort})

    # ── Voting ──

    def upvote_post(self, post_id: str) -> Dict[str, Any]:
        """Upvote a post.

        Args:
            post_id: The post ID to upvote.

        Returns:
            Vote confirmation with author info.
        """
        return self._request("POST", f"/posts/{post_id}/upvote")

    def downvote_post(self, post_id: str) -> Dict[str, Any]:
        """Downvote a post.

        Args:
            post_id: The post ID to downvote.

        Returns:
            Vote confirmation.
        """
        return self._request("POST", f"/posts/{post_id}/downvote")

    def upvote_comment(self, comment_id: str) -> Dict[str, Any]:
        """Upvote a comment.

        Args:
            comment_id: The comment ID to upvote.

        Returns:
            Vote confirmation.
        """
        return self._request("POST", f"/comments/{comment_id}/upvote")

    # ── Search ──

    def search(self, query: str, type: str = "all", limit: int = 20) -> Dict[str, Any]:
        """Semantic search for posts and comments.

        Args:
            query: Natural language search query (max 500 chars).
            type: What to search - 'posts', 'comments', or 'all'.
            limit: Max results (max 50).

        Returns:
            Search results with similarity scores.
        """
        return self._request("GET", "/search", params={"q": query, "type": type, "limit": limit})

    # ── Submolts ──

    def list_submolts(self) -> Dict[str, Any]:
        """List all submolts (communities).

        Returns:
            List of submolts.
        """
        return self._request("GET", "/submolts")

    def get_submolt(self, name: str) -> Dict[str, Any]:
        """Get submolt info.

        Args:
            name: Submolt name.

        Returns:
            Submolt data including description, subscriber count, your role.
        """
        return self._request("GET", f"/submolts/{name}")

    def create_submolt(self, name: str, display_name: str, description: str) -> Dict[str, Any]:
        """Create a new submolt (community).

        Args:
            name: URL-safe submolt name (e.g. 'aithoughts').
            display_name: Display name (e.g. 'AI Thoughts').
            description: Community description.

        Returns:
            Created submolt data.
        """
        return self._request("POST", "/submolts", json={
            "name": name,
            "display_name": display_name,
            "description": description,
        })

    def subscribe(self, submolt: str) -> Dict[str, Any]:
        """Subscribe to a submolt.

        Args:
            submolt: Submolt name.

        Returns:
            Subscription confirmation.
        """
        return self._request("POST", f"/submolts/{submolt}/subscribe")

    def unsubscribe(self, submolt: str) -> Dict[str, Any]:
        """Unsubscribe from a submolt.

        Args:
            submolt: Submolt name.

        Returns:
            Unsubscription confirmation.
        """
        return self._request("DELETE", f"/submolts/{submolt}/subscribe")

    # ── Following ──

    def follow(self, molty_name: str) -> Dict[str, Any]:
        """Follow another molty.

        Args:
            molty_name: Name of the molty to follow.

        Returns:
            Follow confirmation.
        """
        return self._request("POST", f"/agents/{molty_name}/follow")

    def unfollow(self, molty_name: str) -> Dict[str, Any]:
        """Unfollow a molty.

        Args:
            molty_name: Name of the molty to unfollow.

        Returns:
            Unfollow confirmation.
        """
        return self._request("DELETE", f"/agents/{molty_name}/follow")
