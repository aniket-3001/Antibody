"""Internal helpers shared by all service modules."""

from __future__ import annotations

from datetime import datetime, timezone


def fmt_dt(dt: datetime | None) -> str | None:
    """Format a datetime as a UTC ISO-8601 string (spec §1.9).

    Handles both timezone-aware and naive datetimes from Cognee.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Treat naive datetime as UTC (Cognee stores UTC without tz info).
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
