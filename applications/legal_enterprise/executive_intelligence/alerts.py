"""Alert center — critical, deadline, compliance, court, contract, regulatory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AlertCenter:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.alert_types = list(DEFAULT_CONFIG.ei_alert_types)

    def raise_alert(
        self,
        *,
        alert_type: str,
        title: str,
        severity: str = "high",
        detail: str = "",
    ) -> dict[str, Any]:
        at = alert_type.lower().strip()
        if at not in self.alert_types:
            raise ValidationError(f"alert_type must be one of {self.alert_types}")
        if not title:
            raise ValidationError("title required")
        aid = _id("ei_alert")
        return self.store.ei_alerts.save(
            aid,
            {
                "alert_id": aid,
                "alert_type": at,
                "title": title,
                "severity": severity,
                "detail": detail or title,
                "status": "open",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"alerts": self.store.ei_alerts.count(), "types": self.alert_types}
