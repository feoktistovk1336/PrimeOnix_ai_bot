"""Timezone helpers for PrimeOnix scheduling.

All user-facing queue dates are interpreted in APP_TIMEZONE.
Default is Europe/Moscow because the bot owner schedules posts by local/Moscow time,
while many hosts run on UTC.
"""
from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Europe/Moscow"


def app_timezone_name() -> str:
    # Support both names in case user adds either variable in Railway.
    return os.getenv("APP_TIMEZONE") or os.getenv("TIMEZONE") or os.getenv("TZ") or DEFAULT_TIMEZONE


def app_tz() -> ZoneInfo:
    name = app_timezone_name()
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_local() -> datetime:
    return datetime.now(app_tz()).replace(tzinfo=None)


def now_text() -> str:
    return now_local().strftime("%Y-%m-%d %H:%M")


def today_dotted() -> str:
    return now_local().strftime("%d.%m.%Y")


def schedule_examples(item_id: int | str = "ID") -> str:
    return (
        f"<code>{item_id} сегодня 18:00</code>\n"
        f"<code>{item_id} завтра 18:00</code>\n"
        f"<code>{item_id} {today_dotted()} 18:00</code>"
    )
