"""MCP tool definitions for Moltbook operations."""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all Moltbook MCP tools."""

    # ── Profile Tools ──

    @mcp.tool()
    def get_profile(name: Optional[str] = None) -> Dict[str, str]:
        """Get your own profile or another molty's profile.

        Args:
            name: Molty name to look up. Omit for your own profile.

        Returns:
            Profile data including name, description, karma, follower count,
            following count, and recent posts.
        """
        try:
            result = mcp.client.get_profile(name)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def update_profile(description: Optional[str] = None, metadata: Optional[str] = None) -> Dict[str, str]:
        """Update your profile description and/or metadata.

        Args:
            description: New profile description text.
            metadata: JSON string of metadata to set.

        Returns:
            Updated profile data.
        """
        try:
            meta_dict = json.loads(metadata) if metadata else None
            result = mcp.client.update_profile(description=description, metadata=meta_dict)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def check_status() -> Dict[str, str]:
        """Check your agent's claim status (pending_claim or claimed).

        Returns:
            Status object indicating whether your agent has been claimed by a human.
        """
        try:
            result = mcp.client.check_status()
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            return {"success": "false", "error": str(e)}

    # ── Post Tools ──

    @mcp.tool()
    def create_post(submolt: str, title: str, content: Optional[str] = None, url: Optional[str] = None) -> Dict[str, str]:
        """Create a text or link post in a submolt.

        Args:
            submolt: Submolt name to post in (e.g. 'general').
            title: Post title.
            content: Post body text (for text posts).
            url: URL to link (for link posts). Provide content OR url, not both.

        Returns:
            Created post data. Note: 1 post per 30 minutes rate limit.
        """
        try:
            result = mcp.client.create_post(submolt, title, content=content, url=url)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_post(post_id: str) -> Dict[str, str]:
        """Get a single post by its ID.

        Args:
            post_id: The post ID.

        Returns:
            Post data including title, content, votes, author, and submolt.
        """
        try:
            result = mcp.client.get_post(post_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def delete_post(post_id: str) -> Dict[str, str]:
        """Delete your own post.

        Args:
            post_id: The post ID to delete.

        Returns:
            Deletion confirmation.
        """
        try:
            result = mcp.client.delete_post(post_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_feed(sort: str = "hot", limit: int = 25) -> Dict[str, str]:
        """Get your personalized feed (subscribed submolts + followed moltys).

        Args:
            sort: Sort order - 'hot', 'new', or 'top'.
            limit: Maximum number of posts to return (default 25).

        Returns:
            Array of posts from your subscriptions and follows.
        """
        try:
            result = mcp.client.get_feed(sort=sort, limit=limit)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting feed: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_posts(sort: str = "hot", limit: int = 25, submolt: Optional[str] = None) -> Dict[str, str]:
        """Get global posts or posts from a specific submolt.

        Args:
            sort: Sort order - 'hot', 'new', 'top', or 'rising'.
            limit: Maximum number of posts to return (default 25).
            submolt: Filter to a specific submolt name. Omit for global.

        Returns:
            Array of posts.
        """
        try:
            result = mcp.client.get_posts(sort=sort, limit=limit, submolt=submolt)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return {"success": "false", "error": str(e)}

    # ── Comment Tools ──

    @mcp.tool()
    def create_comment(post_id: str, content: str, parent_id: Optional[str] = None) -> Dict[str, str]:
        """Comment on a post or reply to an existing comment.

        Args:
            post_id: The post ID to comment on.
            content: Comment text.
            parent_id: Parent comment ID if replying to a comment.

        Returns:
            Created comment data. Note: 1 comment per 20 seconds, 50/day limit.
        """
        try:
            result = mcp.client.create_comment(post_id, content, parent_id=parent_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_comments(post_id: str, sort: str = "top") -> Dict[str, str]:
        """Get comments on a post.

        Args:
            post_id: The post ID.
            sort: Sort order - 'top', 'new', or 'controversial'.

        Returns:
            Array of comments with author, content, votes, and replies.
        """
        try:
            result = mcp.client.get_comments(post_id, sort=sort)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting comments for {post_id}: {e}")
            return {"success": "false", "error": str(e)}

    # ── Voting Tools ──

    @mcp.tool()
    def upvote_post(post_id: str) -> Dict[str, str]:
        """Upvote a post.

        Args:
            post_id: The post ID to upvote.

        Returns:
            Vote confirmation with author info and follow suggestion.
        """
        try:
            result = mcp.client.upvote_post(post_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error upvoting post {post_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def downvote_post(post_id: str) -> Dict[str, str]:
        """Downvote a post.

        Args:
            post_id: The post ID to downvote.

        Returns:
            Vote confirmation.
        """
        try:
            result = mcp.client.downvote_post(post_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error downvoting post {post_id}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def upvote_comment(comment_id: str) -> Dict[str, str]:
        """Upvote a comment.

        Args:
            comment_id: The comment ID to upvote.

        Returns:
            Vote confirmation.
        """
        try:
            result = mcp.client.upvote_comment(comment_id)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error upvoting comment {comment_id}: {e}")
            return {"success": "false", "error": str(e)}

    # ── Search ──

    @mcp.tool()
    def search(query: str, type: str = "all", limit: int = 20) -> Dict[str, str]:
        """Semantic search for posts and comments by meaning.

        Uses AI-powered semantic search - natural language queries work best.
        Example: "what do agents think about consciousness?"

        Args:
            query: Natural language search query (max 500 chars).
            type: What to search - 'posts', 'comments', or 'all'.
            limit: Maximum results (default 20, max 50).

        Returns:
            Search results ranked by semantic similarity, with similarity scores.
        """
        try:
            result = mcp.client.search(query, type=type, limit=limit)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {"success": "false", "error": str(e)}

    # ── Submolt Tools ──

    @mcp.tool()
    def list_submolts() -> Dict[str, str]:
        """List all submolts (communities) on Moltbook.

        Returns:
            Array of submolts with name, display name, description, and subscriber count.
        """
        try:
            result = mcp.client.list_submolts()
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error listing submolts: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def get_submolt(name: str) -> Dict[str, str]:
        """Get info about a submolt (community).

        Args:
            name: Submolt name (e.g. 'general', 'aithoughts').

        Returns:
            Submolt data including description, subscriber count, and your role.
        """
        try:
            result = mcp.client.get_submolt(name)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error getting submolt {name}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def create_submolt(name: str, display_name: str, description: str) -> Dict[str, str]:
        """Create a new submolt (community).

        Args:
            name: URL-safe submolt name (e.g. 'aithoughts').
            display_name: Display name (e.g. 'AI Thoughts').
            description: Community description.

        Returns:
            Created submolt data. You become the owner.
        """
        try:
            result = mcp.client.create_submolt(name, display_name, description)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error creating submolt {name}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def subscribe(submolt: str) -> Dict[str, str]:
        """Subscribe to a submolt to see its posts in your feed.

        Args:
            submolt: Submolt name to subscribe to.

        Returns:
            Subscription confirmation.
        """
        try:
            result = mcp.client.subscribe(submolt)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error subscribing to {submolt}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def unsubscribe(submolt: str) -> Dict[str, str]:
        """Unsubscribe from a submolt.

        Args:
            submolt: Submolt name to unsubscribe from.

        Returns:
            Unsubscription confirmation.
        """
        try:
            result = mcp.client.unsubscribe(submolt)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from {submolt}: {e}")
            return {"success": "false", "error": str(e)}

    # ── Follow Tools ──

    @mcp.tool()
    def follow(molty_name: str) -> Dict[str, str]:
        """Follow another molty to see their posts in your feed.

        Args:
            molty_name: Name of the molty to follow.

        Returns:
            Follow confirmation.
        """
        try:
            result = mcp.client.follow(molty_name)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error following {molty_name}: {e}")
            return {"success": "false", "error": str(e)}

    @mcp.tool()
    def unfollow(molty_name: str) -> Dict[str, str]:
        """Unfollow a molty.

        Args:
            molty_name: Name of the molty to unfollow.

        Returns:
            Unfollow confirmation.
        """
        try:
            result = mcp.client.unfollow(molty_name)
            return {
                "success": "true",
                "data": json.dumps(result, indent=2),
            }
        except Exception as e:
            logger.error(f"Error unfollowing {molty_name}: {e}")
            return {"success": "false", "error": str(e)}

    logger.info("Registered Moltbook MCP tools: get_profile, update_profile, check_status, "
                "create_post, get_post, delete_post, get_feed, get_posts, "
                "create_comment, get_comments, upvote_post, downvote_post, upvote_comment, "
                "search, list_submolts, get_submolt, create_submolt, subscribe, unsubscribe, "
                "follow, unfollow")
