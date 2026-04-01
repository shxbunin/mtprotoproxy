from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
