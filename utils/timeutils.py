from __future__ import annotations
from datetime import datetime, timezone, timedelta

# Fixed GMT-4 timezone used across the app
GMT4_TZ = timezone(timedelta(hours=-4))


def gmt4_now() -> datetime:
    """Return current datetime locked at GMT-4."""
    return datetime.now(GMT4_TZ)


def gmt4_timestamp() -> str:
    """Current timestamp in GMT-4."""
    return gmt4_now().isoformat(timespec="seconds")
