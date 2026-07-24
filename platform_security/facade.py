"""Security Hardening library facade — Sprint 21.4."""

from __future__ import annotations

from typing import Any

from platform_security.audit import AuditTrail
from platform_security.authentication import IdentitySecurity
from platform_security.authorization import AccessControl
from platform_security.certificates import CertificateStore
from platform_security.compliance import ComplianceFramework
from platform_security.dashboard import SecurityDashboard
from platform_security.encryption import EncryptionLayer
from platform_security.incident_response import IncidentResponse
from platform_security.models import INTEGRATION_TARGETS
from platform_security.monitoring import SecurityMonitoring
from platform_security.policies import PolicyCatalog
from platform_security.rate_limit import RateLimitProtection
from platform_security.secrets import SecretsManager
from platform_security.testing import SecurityTesting
from platform_security.waf import WafEngine
from platform_security.zero_trust import ZeroTrustEngine


class SecurityHardeningLibrary:
    def __init__(self) -> None:
        self.identity = IdentitySecurity()
        self.access = AccessControl()
        self.zero_trust = ZeroTrustEngine()
        self.secrets = SecretsManager()
        self.encryption = EncryptionLayer()
        self.audit = AuditTrail()
        self.monitoring = SecurityMonitoring()
        self.rate_limit = RateLimitProtection()
        self.waf = WafEngine()
        self.policies = PolicyCatalog()
        self.certificates = CertificateStore()
        self.compliance = ComplianceFramework()
        self.incidents = IncidentResponse()
        self.testing = SecurityTesting()
        self.dashboard = SecurityDashboard()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        # fresh components for idempotent bootstrap
        self.__init__()
        auth = self.identity.authenticate(method="oauth2", principal="security.admin", secret="bootstrap")
        self.access.grant_role("security.admin", "admin")
        self.access.define_policy(
            name="org_ops",
            attributes={"organization": "acme", "operation_type": "read"},
            effect="allow",
        )
        authz = self.access.authorize(
            principal="security.admin",
            roles_required=["admin"],
            attributes={"organization": "acme", "operation_type": "read"},
        )
        zt = self.zero_trust.evaluate(
            {
                "user": "security.admin",
                "device": "managed-laptop",
                "token": auth["access_token"],
                "ip": "10.0.0.8",
                "context": "corporate",
                "risk_level": 0.12,
                "security_policy": "default",
            }
        )
        for kind, name, value in (
            ("api_key", "hub-api", "key-hub"),
            ("jwt_secret", "jwt-main", "jwt-secret"),
            ("encryption_key", "aes-main", "aes-key"),
            ("database_password", "db-main", "db-pass"),
            ("cloud_credential", "cloud-main", "cloud-cred"),
            ("ai_provider_key", "openai-main", "ai-key"),
        ):
            self.secrets.put(name=name, kind=kind, value=value)
        enc = self.encryption.encrypt("sensitive-payload", algorithm="aes_256")
        sig = self.encryption.sign("payload", key="aes-key")
        for action in (
            "user_login",
            "ai_action",
            "data_change",
            "role_change",
            "workflow_start",
            "api_access",
            "admin_action",
        ):
            self.audit.record(action=action, actor="security.admin", resource="platform")
        sealed = self.audit.seal()
        alert = self.monitoring.detect(signal="anomalous_request", severity="low")
        rl = self.rate_limit.check(key="api:/health", limit=100)
        waf = self.waf.inspect(path="/api/v1/users", body="ok")
        cert = self.certificates.issue(subject="CN=enterprise-hub")
        compliance = self.compliance.assess()
        tests = self.testing.run_all()
        incident = self.incidents.open(title="Simulated brute-force blocked", severity="medium")
        dash = self.dashboard.render(
            trust_score=zt["trust_score"],
            audit_entries=sealed["entries"],
            alerts=len(self.monitoring.list_alerts()),
            secrets=self.secrets.status()["secrets"],
            compliance_ready=compliance["overall_ready"],
            tests_passed=tests["passed"],
        )
        return {
            "bootstrap": True,
            "session_id": auth["session_id"],
            "auth_methods": self.identity.methods(),
            "authorization_allowed": authz["allowed"],
            "zero_trust_allowed": zt["allowed"],
            "trust_score": zt["trust_score"],
            "secrets": self.secrets.status()["secrets"],
            "encryption_algorithm": enc["algorithm"],
            "signature_ok": bool(sig),
            "audit_tip": sealed["tip_hash"],
            "audit_entries": sealed["entries"],
            "monitoring_alert_id": alert["alert_id"],
            "rate_limit_allowed": rl["allowed"],
            "waf_allowed": waf["allowed"],
            "cert_id": cert["cert_id"],
            "compliance_ready": compliance["overall_ready"],
            "compliance_frameworks": compliance["count"],
            "security_tests_passed": tests["passed"],
            "incident_id": incident["incident_id"],
            "hardening_level": dash["hardening_level"],
            "executive_summary": dash["executive_summary"],
            "policies": len(self.policies.list_all()),
            "integrations": self.integrations(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "identity": self.identity.status(),
            "access": self.access.status(),
            "secrets": self.secrets.status(),
            "audit": self.audit.status(),
            "monitoring": self.monitoring.status(),
        }


security_hardening_library = SecurityHardeningLibrary()
