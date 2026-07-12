# Minimal 5-field cron next-run calculator (UTC).

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _field_matches(field: str, value: int, *, min_value: int, max_value: int) -> bool:
    field = field.strip()
    if field == "*":
        return True
    if field.startswith("*/"):
        step = int(field[2:])
        return value % step == 0
    if "," in field:
        return value in {int(part) for part in field.split(",")}
    if "-" in field:
        start, end = field.split("-", 1)
        return int(start) <= value <= int(end)
    return int(field) == value


def _cron_matches(expression: str, moment: datetime) -> bool:
    parts = expression.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expression}")

    minute, hour, day, month, weekday = parts
    if not _field_matches(minute, moment.minute, min_value=0, max_value=59):
        return False
    if not _field_matches(hour, moment.hour, min_value=0, max_value=23):
        return False
    if not _field_matches(day, moment.day, min_value=1, max_value=31):
        return False
    if not _field_matches(month, moment.month, min_value=1, max_value=12):
        return False

    cron_dow = moment.weekday()
    # Python weekday: Mon=0..Sun=6; cron: Sun=0 or 7, Mon=1..Sat=6
    cron_dow_value = (cron_dow + 1) % 7
    if weekday != "*":
        if not _field_matches(weekday, cron_dow_value, min_value=0, max_value=7):
            return False
    return True


def next_cron_run(expression: str, after: datetime | None = None) -> datetime:
    """Return the next UTC datetime matching a 5-field cron expression."""
    start = after or datetime.now(timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    candidate = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = start + timedelta(days=366)
    while candidate <= limit:
        if _cron_matches(expression, candidate):
            return candidate
        candidate += timedelta(minutes=1)

    raise ValueError(f"No cron match within 366 days for: {expression}")
