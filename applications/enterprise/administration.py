"""Enterprise Administration — RBAC, SSO, audit, compliance (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.config import DEFAULT_CONFIG
from applications.enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseAdministration:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store
        self.providers = list(DEFAULT_CONFIG.auth_providers)

    def define_role(self, *, name: str, permissions: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("role name required")
        rid = _id("role")
        role = {
            "role_id": rid,
            "name": name,
            "permissions": permissions or [],
            "created_at": _now(),
        }
        return self.store.roles.save(rid, role)

    def assign_role(self, *, principal: str, role_id: str) -> dict[str, Any]:
        if self.store.roles.get(role_id) is None:
            raise NotFoundError("role", role_id)
        aid = _id("assign")
        assignment = {
            "assignment_id": aid,
            "principal": principal,
            "role_id": role_id,
            "assigned_at": _now(),
        }
        return self.store.assignments.save(aid, assignment)

    def authenticate(self, *, provider: str, principal: str, credentials: dict[str, Any] | None = None) -> dict[str, Any]:
        if provider not in self.providers:
            raise ValidationError(f"provider must be one of {self.providers}")
        if not principal:
            raise ValidationError("principal required")
        sid = _id("sess")
        session = {
            "session_id": sid,
            "provider": provider,
            "principal": principal,
            "credentials_present": bool(credentials),
            "status": "authenticated",
            "authenticated_at": _now(),
        }
        return self.store.auth_sessions.save(sid, session)

    def audit(self, *, actor: str, action: str, resource: str = "", detail: str = "") -> dict[str, Any]:
        eid = _id("audit")
        event = {
            "audit_id": eid,
            "actor": actor,
            "action": action,
            "resource": resource,
            "detail": detail,
            "at": _now(),
        }
        return self.store.audit_events.save(eid, event)

    def security_alert(self, *, severity: str, message: str, source: str = "security_center") -> dict[str, Any]:
        aid = _id("sec")
        alert = {
            "alert_id": aid,
            "severity": severity,
            "message": message,
            "source": source,
            "status": "open",
            "at": _now(),
        }
        return self.store.security_alerts.save(aid, alert)

    def set_policy(self, *, name: str, rules: dict[str, Any] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("policy name required")
        pid = _id("policy")
        policy = {
            "policy_id": pid,
            "name": name,
            "rules": rules or {},
            "status": "active",
            "created_at": _now(),
        }
        return self.store.policies.save(pid, policy)

    def compliance_check(self, *, framework: str, status: str = "compliant", findings: list[str] | None = None) -> dict[str, Any]:
        cid = _id("comp")
        record = {
            "compliance_id": cid,
            "framework": framework,
            "status": status,
            "findings": findings or [],
            "checked_at": _now(),
        }
        return self.store.compliance_records.save(cid, record)

    def status(self) -> dict[str, Any]:
        return {
            "roles": len(self.store.roles.list_all()),
            "assignments": len(self.store.assignments.list_all()),
            "sessions": len(self.store.auth_sessions.list_all()),
            "audit_events": len(self.store.audit_events.list_all()),
            "policies": len(self.store.policies.list_all()),
            "compliance_records": len(self.store.compliance_records.list_all()),
            "security_alerts": len(self.store.security_alerts.list_all()),
            "providers": self.providers,
        }


enterprise_administration = EnterpriseAdministration()
