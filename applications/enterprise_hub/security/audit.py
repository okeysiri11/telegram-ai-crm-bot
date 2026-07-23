"""Security audit journal."""

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


class SecurityAudit:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(
        self,
        *,
        action: str,
        actor: str,
        subject: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        if not action or not actor:
            raise ValidationError("action and actor required")
        aid = _id("isam_audit")
        return self.store.isam_audit.save(
            aid,
            {
                "audit_id": aid,
                "action": action,
                "actor": actor,
                "subject": subject,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.isam_audit.count()}
