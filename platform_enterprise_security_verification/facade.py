"""Security Verification library facade — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.api_security import APISecurityScanner
from platform_enterprise_security_verification.audit import AuditEngine
from platform_enterprise_security_verification.authn import AuthenticationValidator
from platform_enterprise_security_verification.authz import AuthorizationValidator
from platform_enterprise_security_verification.compliance import ComplianceEngine
from platform_enterprise_security_verification.dashboard import SecurityVerificationDashboard
from platform_enterprise_security_verification.deps import DependencyScanner
from platform_enterprise_security_verification.integrations import SecurityVerificationIntegrations
from platform_enterprise_security_verification.manager import SecurityManager
from platform_enterprise_security_verification.models import PRINCIPLES
from platform_enterprise_security_verification.reports import SecurityReports
from platform_enterprise_security_verification.secrets import SecretScanner
from platform_enterprise_security_verification.tenancy import TenantIsolationValidator
from platform_enterprise_security_verification.vuln import VulnerabilityScanner


class SecurityVerificationLibrary:
    def __init__(self) -> None:
        self.manager = SecurityManager()
        self.authn = AuthenticationValidator()
        self.authz = AuthorizationValidator()
        self.tenancy = TenantIsolationValidator()
        self.api_security = APISecurityScanner()
        self.vuln = VulnerabilityScanner()
        self.secrets = SecretScanner()
        self.deps = DependencyScanner()
        self.audit = AuditEngine()
        self.compliance = ComplianceEngine()
        self.dashboard = SecurityVerificationDashboard()
        self.reports = SecurityReports()
        self.integrations = SecurityVerificationIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        plan = self.manager.plan(release="8.5.0")
        authn = self.authn.validate()
        authz = self.authz.validate()
        tenancy = self.tenancy.validate()
        api = self.api_security.scan()
        vuln = self.vuln.scan()
        secrets = self.secrets.scan()
        deps = self.deps.scan()
        audit = self.audit.collect(
            events=[{"type": t, "ok": True} for t in (
                "login", "logout", "permission_changes", "role_changes",
                "security_events", "failed_authentication", "failed_authorization", "configuration_changes",
            )]
        )
        compliance = self.compliance.assess()
        critical = vuln["critical_count"] + deps["critical_count"]
        score = 100.0 if critical == 0 else max(0.0, 100.0 - critical * 25)
        release_blocked = critical > 0
        reports = self.reports.generate(
            run_id="sec_boot",
            summary={
                "score": score,
                "critical": critical,
                "release_blocked": release_blocked,
                "authn": authn["passed"],
                "authz": authz["passed"],
            },
        )
        dash = self.dashboard.render(
            score=score,
            vulnerabilities=len([c for c in vuln["checks"] if not c["passed"]]),
            critical_issues=critical,
            authentication=authn,
            authorization=authz,
            secrets=secrets,
            dependencies=deps,
            audit_events=len(audit["events"]),
            compliance=compliance,
            recommendations=["keep_security_gate_in_ci"] if not release_blocked else ["fix_critical_before_release"],
            release_blocked=release_blocked,
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "security_verification_ready": True,
            "vulnerability_scanner_ready": True,
            "secret_scanner_ready": True,
            "compliance_ready": True,
            "release_blocked": release_blocked,
            "block_on_critical": True,
            "ci_cd_required": True,
            "duplicates_core_logic": False,
            "duplicates_esh_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
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
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "manager",
                "authn",
                "authz",
                "tenancy",
                "api_security",
                "vuln",
                "secrets",
                "deps",
                "audit",
                "compliance",
                "dashboard",
                "reports",
            ],
            "principles": self.principles(),
            "block_on_critical": True,
        }


security_verification_library = SecurityVerificationLibrary()
