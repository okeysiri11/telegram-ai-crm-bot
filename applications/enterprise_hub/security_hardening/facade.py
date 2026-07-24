"""Security Hardening Suite facade — Sprint 21.4 / v6.0.0-rc4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_security.facade import SecurityHardeningLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SecurityHardeningSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = SecurityHardeningLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = SecurityHardeningLibrary()
        result = self.library.bootstrap()
        bid = _id("esh_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.esh_bootstraps.save(bid, record)
        for entry in self.library.audit.list_all():
            self.store.esh_audit.save(entry["audit_id"], entry)
        for alert in self.library.monitoring.list_alerts():
            self.store.esh_alerts.save(alert["alert_id"], alert)
        for secret in self.library.secrets.list_all():
            self.store.esh_secrets.save(secret["secret_id"], secret)
        dash_id = _id("esh_dash")
        dash = self.library.dashboard.render(
            trust_score=result["trust_score"],
            audit_entries=result["audit_entries"],
            alerts=len(self.library.monitoring.list_alerts()),
            secrets=result["secrets"],
            compliance_ready=result["compliance_ready"],
            tests_passed=result["security_tests_passed"],
        )
        self.store.esh_dashboards.save(dash_id, {"dashboard_id": dash_id, **dash, "rendered_at": _now()})
        record["dashboard_id"] = dash_id
        self.store.esh_bootstraps.save(bid, record)
        return record

    def authenticate(self, *, method: str, principal: str, secret: str = "", mfa_code: str | None = None) -> dict[str, Any]:
        try:
            result = self.library.identity.authenticate(
                method=method, principal=principal, secret=secret, mfa_code=mfa_code
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.esh_sessions.save(result["session_id"], result)
        return result

    def authorize(self, *, principal: str, roles_required: list[str] | None = None, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self.library.access.authorize(
            principal=principal, roles_required=roles_required, attributes=attributes
        )
        aid = _id("esh_authz")
        record = {"authorization_id": aid, **result, "checked_at": _now()}
        self.store.esh_authorizations.save(aid, record)
        return record

    def zero_trust(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self.library.zero_trust.evaluate(context)
        zid = _id("esh_zt")
        record = {"evaluation_id": zid, **result, "evaluated_at": _now()}
        self.store.esh_zero_trust.save(zid, record)
        return record

    def put_secret(self, *, name: str, kind: str, value: str) -> dict[str, Any]:
        try:
            item = self.library.secrets.put(name=name, kind=kind, value=value)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.esh_secrets.save(item["secret_id"], item)
        return item

    def compliance(self) -> dict[str, Any]:
        result = self.library.compliance.assess()
        cid = _id("esh_comp")
        record = {"compliance_id": cid, **result, "assessed_at": _now()}
        self.store.esh_compliance.save(cid, record)
        return record

    def run_tests(self) -> dict[str, Any]:
        result = self.library.testing.run_all()
        tid = _id("esh_test")
        record = {"test_run_id": tid, **result, "run_at": _now()}
        self.store.esh_tests.save(tid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        items = self.store.esh_dashboards.list_all()
        if items:
            return items[-1]
        raise NotFoundError("security dashboard not found; bootstrap first")

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.esh_bootstraps.list_all()),
            "audit": len(self.store.esh_audit.list_all()),
            "secrets": len(self.store.esh_secrets.list_all()),
            "tests": len(self.store.esh_tests.list_all()),
        }


security_hardening = SecurityHardeningSuite()
