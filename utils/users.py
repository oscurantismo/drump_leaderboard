from __future__ import annotations

def normalize_username(username: str | None) -> str:
    """Ensure username starts with '@' and is stripped."""
    if not username:
        return "Anonymous"
    username = str(username).strip()
    if username and not username.startswith("@"): 
        username = "@" + username.lstrip("@")
    return username


def user_log_info(username: str | None, first_name: str = "", last_name: str = "") -> str:
    """Return formatted string for logs with username and full name."""
    username = normalize_username(username)
    full_name = " ".join(part for part in [first_name.strip(), last_name.strip()] if part)
    return f"{username} ({full_name})" if full_name else username
