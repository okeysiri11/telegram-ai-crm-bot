"""Immutable audit trail — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import uuid

from platform_security.models import AUDIT_ACTIONS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditTrail:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []
        self._sealed = False

    def record(self, *, action: str, actor: str, resource: str = "", details: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._sealed:
            raise RuntimeError("audit trail is sealed")
        if action not in AUDIT_ACTIONS:
            raise ValueError(f"invalid audit action: {action}")
        prev = self._entries[-1]["entry_hash"] if self._entries else "genesis"
        eid = f"aud_{uuid.uuid4().hex[:12]}"
        payload = {
            "audit_id": eid,
            "action": action,
            "actor": actor,
            "resource": resource,
            "details": details or {},
            "prev_hash": prev,
            "recorded_at": _now(),
            "immutable": True,
        }
        digest = hashlib.sha256(f"{prev}:{action}:{actor}:{resource}:{payload['recorded_at']}".encode()).hexdigest()
        payload["entry_hash"] = digest
        self._entries.append(payload)
        return payload

    def seal(self) -> dict[str, Any]:
        self._sealed = True
        tip = self._entries[-1]["entry_hash"] if self._entries else "empty"
        return {"sealed": True, "entries": len(self._entries), "tip_hash": tip}

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def status(self) -> dict[str, Any]:
        return {"entries": len(self._entries), "sealed": self._sealed}
