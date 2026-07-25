"""Security Verification Suite — Sprint 25.5 / v8.5.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_security_verification.facade import SecurityVerificationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SecurityVerificationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = SecurityVerificationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = SecurityVerificationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("esv_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.esv_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("authn", "esv_authn", "esv_authn"),
            ("authz", "esv_authz", "esv_authz"),
            ("vuln", "esv_vulns", "esv_vuln"),
            ("secrets", "esv_secrets", "esv_sec"),
            ("deps", "esv_deps", "esv_dep"),
            ("compliance", "esv_compliance", "esv_cmp"),
            ("reports", "esv_reports", "esv_rep"),
            ("dashboard", "esv_dashboards", "esv_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.esv_bootstraps.save(bid, record)
        return record

    def run_gate(
        self,
        *,
        release: str | None = None,
        vuln_findings: list[dict[str, Any]] | None = None,
        secret_hits: list[dict[str, Any]] | None = None,
        cves: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        release = release or DEFAULT_CONFIG.application_version
        plan = self.library.manager.plan(release=release)
        authn = self.library.authn.validate()
        authz = self.library.authz.validate()
        tenancy = self.library.tenancy.validate()
        api = self.library.api_security.scan()
        try:
            vuln = self.library.vuln.scan(findings=vuln_findings)
            secrets = self.library.secrets.scan(hits=secret_hits)
            deps = self.library.deps.scan(cves=cves)
            compliance = self.library.compliance.assess()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        audit = self.library.audit.collect(
            events=[{"type": t} for t in (
                "login", "logout", "permission_changes", "role_changes",
                "security_events", "failed_authentication", "failed_authorization", "configuration_changes",
            )]
        )
        critical = vuln["critical_count"] + deps["critical_count"]
        release_blocked = critical > 0 or not secrets["passed"]
        score = 100.0 if not release_blocked else max(0.0, 100.0 - critical * 25 - (0 if secrets["passed"] else 20))
        reports = self.library.reports.generate(
            run_id=_id("esv_run"),
            summary={"score": score, "critical": critical, "release_blocked": release_blocked},
        )
        dash = self.library.dashboard.render(
            score=score,
            vulnerabilities=sum(1 for c in vuln["checks"] if not c["passed"]),
            critical_issues=critical,
            authentication=authn,
            authorization=authz,
            secrets=secrets,
            dependencies=deps,
            audit_events=len(audit["events"]),
            compliance=compliance,
            recommendations=(
                ["fix_critical_before_release"] if release_blocked else ["security_gate_passed"]
            ),
            release_blocked=release_blocked,
        )
        rid = _id("esv_run")
        record = {
            "run_id": rid,
            "plan": plan,
            "authn": authn,
            "authz": authz,
            "tenancy": tenancy,
            "api": api,
            "vuln": vuln,
            "secrets": secrets,
            "deps": deps,
            "audit": audit,
            "compliance": compliance,
            "reports": reports,
            "dashboard": dash,
            "release_blocked": release_blocked,
            "production_allowed": not release_blocked,
            "created_at": _now(),
        }
        self.store.esv_runs.save(rid, record)
        did = _id("esv_dash")
        self.store.esv_dashboards.save(did, {"dashboard_id": did, **dash, "created_at": _now()})
        rep_id = _id("esv_rep")
        self.store.esv_reports.save(rep_id, {"report_id": rep_id, **reports, "created_at": _now()})
        return record

    def dashboard(self) -> dict[str, Any]:
        runs = self.store.esv_runs.list_all()
        if runs:
            return runs[-1].get("dashboard") or self.run_gate()["dashboard"]
        return self.run_gate()["dashboard"]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.esv_bootstraps.list_all()),
            "runs": len(self.store.esv_runs.list_all()),
            "block_on_critical": True,
        }


security_verification = SecurityVerificationSuite()
