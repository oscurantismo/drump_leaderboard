from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TORONTO_TZ = ZoneInfo("America/Toronto")


def toronto_now() -> datetime:
    """Return current datetime in the Toronto timezone."""
    return datetime.now(TORONTO_TZ)


def utc_timestamp() -> str:
    """Current timestamp in UTC derived from Toronto time."""
    return (
        toronto_now()
        .astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
