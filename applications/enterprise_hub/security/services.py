"""ISAM dashboards and MFA helper — Sprint 30.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.security.mfa import challenge_mfa
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MFAService:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def challenge(self, *, method: str, subject: str, code: str = "") -> dict[str, Any]:
        return challenge_mfa(self.store, method=method, subject=subject, code=code)

    def set_user_mfa(self, *, identity_id: str, enabled: bool) -> dict[str, Any]:
        identity = self.store.isam_identities.get(identity_id)
        if identity is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        identity["mfa_enabled"] = bool(enabled)
        identity["at"] = _now()
        self.store.isam_identities.save(identity_id, identity)
        return {"identity_id": identity_id, "mfa_enabled": bool(enabled)}

    def set_org_policy(self, *, organization_id: str, require_mfa: bool) -> dict[str, Any]:
        pid = f"isam_pol_mfa_{organization_id}"
        return self.store.isam_policies.save(
            pid,
            {
                "policy_id": pid,
                "kind": "mfa_required",
                "organization_id": organization_id,
                "require_mfa": bool(require_mfa),
                "at": _now(),
            },
        )

    def org_requires_mfa(self, *, organization_id: str) -> bool:
        for pol in self.store.isam_policies.list_all():
            if (
                isinstance(pol, dict)
                and pol.get("kind") == "mfa_required"
                and pol.get("organization_id") == organization_id
            ):
                return bool(pol.get("require_mfa"))
        return False

    def required_for(self, *, identity_id: str, organization_id: str = "") -> dict[str, Any]:
        identity = self.store.isam_identities.get(identity_id) or {}
        user_enabled = bool(identity.get("mfa_enabled"))
        org_required = self.org_requires_mfa(organization_id=organization_id) if organization_id else False
        return {
            "user_enabled": user_enabled,
            "org_required": org_required,
            "must_challenge": user_enabled or org_required,
            "optional": not org_required,
        }

    def status(self) -> dict[str, Any]:
        enabled_users = sum(
            1
            for i in self.store.isam_identities.list_all()
            if isinstance(i, dict) and i.get("mfa_enabled")
        )
        return {
            "challenges": self.store.isam_mfa.count(),
            "users_with_mfa": enabled_users,
            "methods": ["totp", "email", "sms", "hardware_key", "backup_codes"],
        }


class SecurityDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.isam_dashboard_types) + ["owner_security"]

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt == "owner_security":
            return self.owner_security_snapshot()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "identity": {
                "identities": self.store.isam_identities.count(),
                "role_assigns": self.store.isam_role_assigns.count(),
            },
            "sessions": {
                "sessions": self.store.isam_sessions.count(),
                "tokens": self.store.isam_tokens.count(),
                "api_keys": self.store.isam_api_keys.count(),
            },
            "access": {
                "authz": self.store.isam_authz.count(),
                "permissions": self.store.isam_permissions.count(),
                "policies": self.store.isam_policies.count(),
            },
            "monitoring": {
                "intrusions": self.store.isam_intrusions.count(),
                "anomalies": self.store.isam_anomalies.count(),
                "risks": self.store.isam_risks.count(),
            },
            "audit": {
                "entries": self.store.isam_audit.count(),
                "auth_events": self.store.isam_auth_events.count(),
                "mfa": self.store.isam_mfa.count(),
            },
        }.get(dt, {})
        did = _id("isam_dash")
        return self.store.isam_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def owner_security_snapshot(self) -> dict[str, Any]:
        sessions = [
            s
            for s in self.store.isam_sessions.list_all()
            if isinstance(s, dict) and s.get("status") == "active"
        ]
        auth_events = [
            e for e in self.store.isam_auth_events.list_all() if isinstance(e, dict)
        ]
        failed = [e for e in auth_events if e.get("success") is False]
        audit = [a for a in self.store.isam_audit.list_all() if isinstance(a, dict)]
        tokens = [
            t
            for t in self.store.isam_tokens.list_all()
            if isinstance(t, dict) and t.get("status") == "active"
        ]
        return {
            "dashboard_type": "owner_security",
            "active_sessions": len(sessions),
            "sessions": sessions[-20:],
            "failed_logins": len(failed),
            "failed_login_events": failed[-20:],
            "security_events": audit[-30:],
            "auth_events": auth_events[-30:],
            "api_status": {"ok": True, "tokens_active": len(tokens)},
            "token_status": {
                "active": len(tokens),
                "total": self.store.isam_tokens.count(),
            },
            "rate_limit_events": [],
            "audit_events": audit[-40:],
            "mfa": {
                "challenges": self.store.isam_mfa.count(),
            },
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.isam_dashboards.count(), "types": self.types}
