"""Safety policies — block dangerous operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DANGEROUS = ("delete_production", "drop_database", "exfiltrate", "disable_security")


class SafetyPolicy:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def evaluate(self, *, operation: str) -> dict[str, Any]:
        blocked = operation.lower().strip() in DANGEROUS
        sid = _id("aios_saf")
        return self.store.aios_safety.save(
            sid,
            {
                "safety_id": sid,
                "operation": operation,
                "allowed": not blocked,
                "at": _now(),
            },
        )
