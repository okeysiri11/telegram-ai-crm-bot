"""Session manager — multi-session, devices, trust, revoke-all — Sprint 30.1."""

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
        remember_me: bool = False,
        trusted: bool = False,
        browser: str = "",
    ) -> dict[str, Any]:
        if not identity_id:
            raise ValidationError("identity_id required")
        if self.store.isam_identities.get(identity_id) is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        ttl = int(ttl_seconds)
        if remember_me:
            ttl = max(ttl, 30 * 24 * 3600)
        sid = _id("isam_sess")
        return self.store.isam_sessions.save(
            sid,
            {
                "session_id": sid,
                "identity_id": identity_id,
                "device": device,
                "browser": browser,
                "ip": ip,
                "ttl_seconds": ttl,
                "remember_me": bool(remember_me),
                "trusted": bool(trusted),
                "status": "active",
                "last_activity": _now(),
                "at": _now(),
            },
        )

    def list_for_identity(self, *, identity_id: str) -> list[dict[str, Any]]:
        return [
            s
            for s in self.store.isam_sessions.list_all()
            if isinstance(s, dict)
            and s.get("identity_id") == identity_id
            and s.get("status") == "active"
        ]

    def terminate(self, *, session_id: str) -> dict[str, Any]:
        sess = self.store.isam_sessions.get(session_id)
        if sess is None:
            raise NotFoundError(f"session not found: {session_id}")
        sess["status"] = "terminated"
        sess["at"] = _now()
        return self.store.isam_sessions.save(session_id, sess)

    def terminate_all(self, *, identity_id: str) -> dict[str, Any]:
        revoked = 0
        for sess in self.list_for_identity(identity_id=identity_id):
            self.terminate(session_id=sess["session_id"])
            revoked += 1
        return {"identity_id": identity_id, "revoked": revoked}

    def trust_device(self, *, session_id: str, trusted: bool = True) -> dict[str, Any]:
        sess = self.store.isam_sessions.get(session_id)
        if sess is None:
            raise NotFoundError(f"session not found: {session_id}")
        sess["trusted"] = bool(trusted)
        sess["at"] = _now()
        return self.store.isam_sessions.save(session_id, sess)

    def touch(self, *, session_id: str) -> dict[str, Any]:
        sess = self.store.isam_sessions.get(session_id)
        if sess is None:
            raise NotFoundError(f"session not found: {session_id}")
        sess["last_activity"] = _now()
        return self.store.isam_sessions.save(session_id, sess)

    def last_login(self, *, identity_id: str) -> dict[str, Any] | None:
        events = [
            e
            for e in self.store.isam_auth_events.list_all()
            if isinstance(e, dict)
            and e.get("identity_id") == identity_id
            and e.get("success") is True
        ]
        if not events:
            return None
        events.sort(key=lambda e: str(e.get("at") or ""), reverse=True)
        return events[0]

    def status(self) -> dict[str, Any]:
        active = sum(
            1
            for s in self.store.isam_sessions.list_all()
            if isinstance(s, dict) and s.get("status") == "active"
        )
        trusted = sum(
            1
            for s in self.store.isam_sessions.list_all()
            if isinstance(s, dict) and s.get("status") == "active" and s.get("trusted")
        )
        return {
            "sessions": self.store.isam_sessions.count(),
            "active": active,
            "trusted_devices": trusted,
        }
