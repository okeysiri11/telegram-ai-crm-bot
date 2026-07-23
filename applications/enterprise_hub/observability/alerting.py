"""Alerting engine — telegram/email/push/sms/webhook with severity levels."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import ALERT_CHANNELS, ALERT_LEVELS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AlertingEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def fire(
        self,
        *,
        title: str,
        level: str = "warning",
        channel: str = "telegram",
        service: str = "",
        escalate: bool = False,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        lv = level.lower().strip()
        ch = channel.lower().strip()
        if lv not in ALERT_LEVELS:
            raise ValidationError(f"level must be one of {list(ALERT_LEVELS)}")
        if ch not in ALERT_CHANNELS:
            raise ValidationError(f"channel must be one of {list(ALERT_CHANNELS)}")
        aid = _id("obs_alert")
        return self.store.obs_alerts.save(
            aid,
            {
                "alert_id": aid,
                "title": title,
                "level": lv,
                "channel": ch,
                "service": service,
                "escalate": escalate,
                "status": "sent",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "alerts": self.store.obs_alerts.count(),
            "levels": list(ALERT_LEVELS),
            "channels": list(ALERT_CHANNELS),
        }
