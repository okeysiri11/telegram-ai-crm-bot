"""ISAM Suite facade — Sprint 19.8."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.security.access_control import AccessControl
from applications.enterprise_hub.security.api_keys import APIKeyManager
from applications.enterprise_hub.security.audit import SecurityAudit
from applications.enterprise_hub.security.authentication import AuthenticationService
from applications.enterprise_hub.security.authorization import AuthorizationService
from applications.enterprise_hub.security.identity_manager import IdentityManager
from applications.enterprise_hub.security.monitoring import (
    AnomalyDetector,
    IntrusionDetector,
    RiskAnalyzer,
)
from applications.enterprise_hub.security.permissions import PermissionEngine
from applications.enterprise_hub.security.policy_engine import PolicyEngine
from applications.enterprise_hub.security.roles import RoleRegistry
from applications.enterprise_hub.security.services import MFAService, SecurityDashboard
from applications.enterprise_hub.security.session_manager import SessionManager
from applications.enterprise_hub.security.token_manager import TokenManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class SecuritySuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.identity = IdentityManager(self.store)
        self.authentication = AuthenticationService(self.store)
        self.authorization = AuthorizationService(self.store)
        self.access = AccessControl(self.store)
        self.permissions = PermissionEngine(self.store)
        self.roles = RoleRegistry(self.store)
        self.policies = PolicyEngine(self.store)
        self.sessions = SessionManager(self.store)
        self.tokens = TokenManager(self.store)
        self.api_keys = APIKeyManager(self.store)
        self.mfa = MFAService(self.store)
        self.audit = SecurityAudit(self.store)
        self.intrusion = IntrusionDetector(self.store)
        self.anomaly = AnomalyDetector(self.store)
        self.risk = RiskAnalyzer(self.store)
        self.dashboard = SecurityDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        admin = self.identity.register(
            subject="admin@bidex.io",
            identity_type="user",
            roles=["super_admin"],
            attributes={"name": "Platform Admin"},
        )
        owner = self.identity.register(
            subject="owner@bidex.io",
            identity_type="user",
            roles=["company_owner"],
        )
        manager = self.identity.register(
            subject="manager@bidex.io",
            identity_type="user",
            roles=["manager"],
        )
        employee = self.identity.register(
            subject="employee@bidex.io",
            identity_type="user",
            roles=["employee"],
        )
        auditor = self.identity.register(
            subject="auditor@bidex.io",
            identity_type="user",
            roles=["auditor"],
        )
        agent = self.identity.register(
            subject="finance_agent",
            identity_type="ai_agent",
            roles=["ai_agent"],
        )
        svc = self.identity.register(
            subject="stripe_connector",
            identity_type="service_account",
            roles=["integration_service"],
        )
        ext = self.identity.register(
            subject="ldap://corp.bidex.io",
            identity_type="external_system",
            roles=["read_only"],
        )

        login = self.authentication.login(subject="admin@bidex.io", provider="local", secret="x")
        oauth = self.authentication.login(subject="owner@bidex.io", provider="oauth2")
        jwt_login = self.authentication.login(subject="manager@bidex.io", provider="jwt")

        role_asg = self.roles.assign(identity_id=employee["identity_id"], role="read_only")
        perm = self.permissions.grant(identity_id=manager["identity_id"], permission="approve")
        resolved = self.permissions.resolve(identity_id=admin["identity_id"])
        authz = self.authorization.authorize(
            identity_id=manager["identity_id"], permission="approve", mode="rbac"
        )
        abac = self.access.check(
            identity_id=employee["identity_id"],
            permission="view",
            mode="abac",
            attributes={"department": "ops"},
        )

        mfa_totp = self.mfa.challenge(method="totp", subject="admin@bidex.io", code="123456")
        mfa_email = self.mfa.challenge(method="email", subject="owner@bidex.io")
        mfa_sms = self.mfa.challenge(method="sms", subject="manager@bidex.io")
        mfa_hw = self.mfa.challenge(method="hardware_key", subject="admin@bidex.io")
        mfa_bk = self.mfa.challenge(method="backup_codes", subject="admin@bidex.io")

        sess = self.sessions.create(
            identity_id=admin["identity_id"], device="macos", ip="10.0.0.8", ttl_seconds=7200
        )
        sess2 = self.sessions.create(identity_id=employee["identity_id"], device="iphone", ip="10.0.0.9")
        term = self.sessions.terminate(session_id=sess2["session_id"])

        tok_access = self.tokens.issue(identity_id=admin["identity_id"], token_type="access")
        tok_refresh = self.tokens.issue(identity_id=admin["identity_id"], token_type="refresh")
        tok_api = self.tokens.issue(identity_id=svc["identity_id"], token_type="api")
        tok_pat = self.tokens.issue(identity_id=owner["identity_id"], token_type="personal_access")
        rot = self.tokens.rotate(token_id=tok_access["token_id"])
        rev = self.tokens.revoke(token_id=tok_pat["token_id"])

        key = self.api_keys.create(identity_id=svc["identity_id"], name="stripe-prod")
        key_rev = self.api_keys.revoke(key_id=key["key_id"])
        # re-create active key after revoke demo
        key2 = self.api_keys.create(identity_id=svc["identity_id"], name="stripe-prod-v2")

        pol_ip = self.policies.create(
            kind="ip", name="corp-allowlist", rule={"allowlist": ["10.0.0.8", "10.0.0.9"]}
        )
        pol_time = self.policies.create(kind="time", name="business-hours", rule={"start": "09:00", "end": "18:00"})
        pol_geo = self.policies.create(kind="geo", name="eu-only", rule={"regions": ["EU"]})
        pol_dev = self.policies.create(kind="device", name="trusted-devices", rule={"trusted": ["macos"]})
        pol_role = self.policies.create(kind="role", name="admin-gate", rule={"roles": ["super_admin"]})
        pol_co = self.policies.create(
            kind="company", name="bidex-policy", rule={"company": "Bidex"}, company_id="BIDEX"
        )
        peval = self.policies.evaluate(
            policy_id=pol_ip["policy_id"], context={"ip": "10.0.0.8"}
        )

        intr = self.intrusion.flag(
            subject="unknown@evil.io", kind="brute_force", detail="10 failed logins", severity="high"
        )
        anom = self.anomaly.flag(
            subject=agent["subject"], kind="ai_agent_anomaly", detail="unusual tool spam"
        )
        risk = self.risk.score(
            subject="unknown@evil.io", factors={"failures": 0.8, "new_device": 0.5}
        )

        aud1 = self.audit.record(action="login", actor="admin@bidex.io", subject=admin["identity_id"])
        aud2 = self.audit.record(action="role_change", actor="admin@bidex.io", subject=employee["identity_id"])
        aud3 = self.audit.record(action="token_issue", actor="system", subject=tok_access["token_id"])
        aud4 = self.audit.record(action="user_deactivate", actor="admin@bidex.io", subject=ext["identity_id"])
        deactivated = self.identity.deactivate(identity_id=ext["identity_id"])

        dash_i = self.dashboard.render(dashboard_type="identity")
        dash_s = self.dashboard.render(dashboard_type="sessions")
        dash_a = self.dashboard.render(dashboard_type="access")
        dash_m = self.dashboard.render(dashboard_type="monitoring")
        dash_au = self.dashboard.render(dashboard_type="audit")

        return {
            "bootstrap": True,
            "identity_admin_id": admin["identity_id"],
            "identity_owner_id": owner["identity_id"],
            "identity_manager_id": manager["identity_id"],
            "identity_employee_id": employee["identity_id"],
            "identity_auditor_id": auditor["identity_id"],
            "identity_ai_agent_id": agent["identity_id"],
            "identity_service_id": svc["identity_id"],
            "identity_external_id": ext["identity_id"],
            "login_id": login["auth_id"],
            "oauth_id": oauth["auth_id"],
            "jwt_login_id": jwt_login["auth_id"],
            "role_assignment_id": role_asg["assignment_id"],
            "permission_id": perm["permission_id"],
            "permission_resolution_id": resolved["resolution_id"],
            "authz_id": authz["authz_id"],
            "abac_id": abac["authz_id"],
            "mfa_totp_id": mfa_totp["mfa_id"],
            "mfa_email_id": mfa_email["mfa_id"],
            "mfa_sms_id": mfa_sms["mfa_id"],
            "mfa_hardware_id": mfa_hw["mfa_id"],
            "mfa_backup_id": mfa_bk["mfa_id"],
            "session_id": sess["session_id"],
            "session_terminated_id": term["session_id"],
            "token_access_id": tok_access["token_id"],
            "token_refresh_id": tok_refresh["token_id"],
            "token_api_id": tok_api["token_id"],
            "token_rotated_id": rot["token_id"],
            "token_revoked_id": rev["token_id"],
            "api_key_id": key2["key_id"],
            "api_key_revoked_id": key_rev["key_id"],
            "policy_ip_id": pol_ip["policy_id"],
            "policy_time_id": pol_time["policy_id"],
            "policy_geo_id": pol_geo["policy_id"],
            "policy_device_id": pol_dev["policy_id"],
            "policy_role_id": pol_role["policy_id"],
            "policy_company_id": pol_co["policy_id"],
            "policy_eval_id": peval["evaluation_id"],
            "intrusion_id": intr["intrusion_id"],
            "anomaly_id": anom["anomaly_id"],
            "risk_id": risk["risk_id"],
            "audit_login_id": aud1["audit_id"],
            "audit_role_id": aud2["audit_id"],
            "audit_token_id": aud3["audit_id"],
            "audit_deactivate_id": aud4["audit_id"],
            "deactivated_id": deactivated["identity_id"],
            "dashboard_identity_id": dash_i["dashboard_id"],
            "dashboard_sessions_id": dash_s["dashboard_id"],
            "dashboard_access_id": dash_a["dashboard_id"],
            "dashboard_monitoring_id": dash_m["dashboard_id"],
            "dashboard_audit_id": dash_au["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "identity": self.identity.status(),
            "authentication": self.authentication.status(),
            "authorization": self.authorization.status(),
            "access": self.access.status(),
            "permissions": self.permissions.status(),
            "roles": self.roles.status(),
            "policies": self.policies.status(),
            "sessions": self.sessions.status(),
            "tokens": self.tokens.status(),
            "api_keys": self.api_keys.status(),
            "mfa": self.mfa.status(),
            "audit": self.audit.status(),
            "intrusion": self.intrusion.status(),
            "anomaly": self.anomaly.status(),
            "risk": self.risk.status(),
            "dashboard": self.dashboard.status(),
        }


isam = SecuritySuite()
