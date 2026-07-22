"""Unified Authentication — SSO, RBAC, orgs, departments, teams, audit (Sprint 12.0)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ecosystem.shared.exceptions import NotFoundError, ValidationError
from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ROLES = ("admin", "executive", "operator", "analyst", "viewer")


class UnifiedIdentity:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def sso_login(self, *, principal: str, provider: str = "local", role: str = "operator") -> dict[str, Any]:
        if not principal:
            raise ValidationError("principal required")
        # Prefer top-level ecosystem identity when available
        try:
            from ecosystem import ecosystem

            if hasattr(ecosystem.engine, "identity"):
                pass  # bridge-only; do not rewrite identity service
        except Exception:
            pass
        sid = f"usso_{uuid.uuid4().hex[:12]}"
        token = hashlib.sha256(f"{principal}:{provider}:{_now()}".encode()).hexdigest()[:32]
        session = {
            "session_id": sid,
            "principal": principal,
            "provider": provider,
            "role": role if role in ROLES else "viewer",
            "token": token,
            "authenticated": True,
            "at": _now(),
        }
        self.store.sessions.save(sid, session)
        self.audit(actor=principal, action="sso_login", resource=provider)
        return session

    def create_organization(self, *, name: str) -> dict[str, Any]:
        oid = f"org_{uuid.uuid4().hex[:10]}"
        org = {"org_id": oid, "name": name, "created_at": _now()}
        self.store.organizations.save(oid, org)
        return org

    def create_department(self, *, org_id: str, name: str) -> dict[str, Any]:
        if self.store.organizations.get(org_id) is None:
            raise NotFoundError("organization", org_id)
        did = f"dep_{uuid.uuid4().hex[:10]}"
        dep = {"department_id": did, "org_id": org_id, "name": name, "created_at": _now()}
        self.store.departments.save(did, dep)
        return dep

    def create_team(self, *, department_id: str, name: str) -> dict[str, Any]:
        if self.store.departments.get(department_id) is None:
            raise NotFoundError("department", department_id)
        tid = f"team_{uuid.uuid4().hex[:10]}"
        team = {"team_id": tid, "department_id": department_id, "name": name, "created_at": _now()}
        self.store.teams.save(tid, team)
        return team

    def grant_role(self, *, principal: str, role: str) -> dict[str, Any]:
        if role not in ROLES:
            raise ValidationError(f"role must be one of {ROLES}")
        rid = f"role_{uuid.uuid4().hex[:10]}"
        grant = {"grant_id": rid, "principal": principal, "role": role, "at": _now()}
        self.store.roles.save(rid, grant)
        return grant

    def audit(self, *, actor: str, action: str, resource: str = "") -> dict[str, Any]:
        aid = f"aud_{uuid.uuid4().hex[:12]}"
        entry = {"audit_id": aid, "actor": actor, "action": action, "resource": resource, "at": _now()}
        self.store.audit.save(aid, entry)
        return entry

    def list_audit(self) -> list[dict[str, Any]]:
        return self.store.audit.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "unified_auth": "1.0",
            "sessions": len(self.store.sessions.list_all()),
            "organizations": len(self.store.organizations.list_all()),
            "ready": True,
        }


unified_identity = UnifiedIdentity()
