# Cron manager — timezone-aware cron scheduling.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from platform_jobs.exceptions import SchedulerError

logger = logging.getLogger(__name__)


class CronManager:
    @staticmethod
    def next_run(cron_expression: str, *, after: datetime | None = None, tz: str = "UTC") -> float:
        from services.scheduler_cron import next_cron_run

        try:
            zone = ZoneInfo(tz)
        except Exception as exc:
            raise SchedulerError(f"Invalid timezone: {tz}") from exc

        utc_after = after or datetime.now(timezone.utc)
        if utc_after.tzinfo is None:
            utc_after = utc_after.replace(tzinfo=timezone.utc)

        local_after = utc_after.astimezone(zone)
        next_local = next_cron_run(cron_expression, local_after)
        next_utc = next_local.astimezone(timezone.utc)
        return next_utc.timestamp()

    @staticmethod
    def validate(cron_expression: str) -> bool:
        from services.scheduler_cron import next_cron_run

        try:
            next_cron_run(cron_expression)
            return True
        except Exception:
            return False


cron_manager = CronManager()
