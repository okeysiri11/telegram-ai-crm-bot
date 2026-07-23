"""ISAM dashboards and MFA helper."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.security.mfa import challenge_mfa
from applications.enterprise_hub.shared.exceptions import ValidationError
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

    def status(self) -> dict[str, Any]:
        return {"challenges": self.store.isam_mfa.count()}


class SecurityDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.isam_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
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

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.isam_dashboards.count(), "types": self.types}
