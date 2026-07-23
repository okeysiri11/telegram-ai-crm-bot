"""Intrusion detection — brute force, suspicious logins."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntrusionDetector:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def flag(
        self,
        *,
        subject: str,
        kind: str = "brute_force",
        detail: str = "",
        severity: str = "medium",
    ) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        iid = _id("isam_intr")
        return self.store.isam_intrusions.save(
            iid,
            {
                "intrusion_id": iid,
                "subject": subject,
                "kind": kind,
                "detail": detail,
                "severity": severity,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"events": self.store.isam_intrusions.count()}
