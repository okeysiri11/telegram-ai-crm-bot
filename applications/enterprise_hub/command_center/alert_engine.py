from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.command_center.models import ALERT_KINDS, ALERT_SEVERITIES
from applications.enterprise_hub.command_center.notification_center import NotificationCenter


class AlertEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.notifications = NotificationCenter(self.store)

    def raise_alert(
        self,
        *,
        kind: str,
        severity: str = "warning",
        message: str,
        source: str = "command_center",
    ) -> dict[str, Any]:
        if kind not in ALERT_KINDS:
            raise ValidationError(f"invalid alert kind: {kind}")
        if severity not in ALERT_SEVERITIES:
            raise ValidationError(f"invalid severity: {severity}")
        if not message:
            raise ValidationError("message is required")
        aid = _id("ecc_alert")
        record = {
            "alert_id": aid,
            "kind": kind,
            "severity": severity,
            "message": message,
            "source": source,
            "status": "open",
            "raised_at": _now(),
        }
        self.store.ecc_alerts.save(aid, record)
        self.notifications.notify(title=f"[{severity}] {kind}", body=message, channel="alerts")
        return record

    def list_open(self) -> list[dict[str, Any]]:
        return [a for a in self.store.ecc_alerts.list_all() if a.get("status") == "open"]

    def status(self) -> dict[str, Any]:
        items = self.store.ecc_alerts.list_all()
        return {
            "alerts": len(items),
            "open": sum(1 for a in items if a.get("status") == "open"),
            "critical": sum(1 for a in items if a.get("severity") == "critical"),
        }
