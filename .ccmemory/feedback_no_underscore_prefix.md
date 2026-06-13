---
name: No underscore prefixes or suffixes on names
description: User strongly dislikes underscore-prefixed or suffixed variable and function names (e.g., _foo, foo_)
type: feedback
---

Never use underscore prefixes or suffixes on variable or function names. This includes leading underscores like `_admin_request` or `_get_sync_token`, and trailing underscores like `foo_`.

**Why:** The user finds this naming convention detestable. This is a strong, non-negotiable preference.

**How to apply:** When writing any code — Python, JS, or otherwise — avoid `_` prefixes/suffixes on all names. For "private" or "internal" methods, just use a descriptive name without the underscore. For example, use `admin_request` instead of `_admin_request`.
