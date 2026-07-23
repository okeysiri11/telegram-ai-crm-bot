"""Session manager — active sessions, devices, IP, TTL, logout."""

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


class SessionManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        identity_id: str,
        device: str = "unknown",
        ip: str = "",
        ttl_seconds: int = 3600,
    ) -> dict[str, Any]:
        if not identity_id:
            raise ValidationError("identity_id required")
        if self.store.isam_identities.get(identity_id) is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        sid = _id("isam_sess")
        return self.store.isam_sessions.save(
            sid,
            {
                "session_id": sid,
                "identity_id": identity_id,
                "device": device,
                "ip": ip,
                "ttl_seconds": int(ttl_seconds),
                "status": "active",
                "at": _now(),
            },
        )

    def terminate(self, *, session_id: str) -> dict[str, Any]:
        sess = self.store.isam_sessions.get(session_id)
        if sess is None:
            raise NotFoundError(f"session not found: {session_id}")
        sess["status"] = "terminated"
        sess["at"] = _now()
        return self.store.isam_sessions.save(session_id, sess)

    def status(self) -> dict[str, Any]:
        active = sum(
            1
            for s in self.store.isam_sessions.list_all()
            if isinstance(s, dict) and s.get("status") == "active"
        )
        return {"sessions": self.store.isam_sessions.count(), "active": active}
