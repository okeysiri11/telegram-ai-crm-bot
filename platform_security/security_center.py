# Enterprise Security Center — Sprint 32.4.
# Single SoR for platform security capabilities. Extends ESH; does not replace ISAM.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_security.anti_parsing import AntiParsingProtection
from platform_security.api_gateway_policy import ApiGatewayPolicy
from platform_security.audit_center import AuditCenter
from platform_security.ai_security_center import AiSecurityCenter
from platform_security.external_ai_guard import ExternalAiGuard
from platform_security.facade import SecurityHardeningLibrary, security_hardening_library
from platform_security.incident_center import IncidentCenter
from platform_security.knowledge_security import KnowledgeSecurity
from platform_security.zero_trust import ZeroTrustEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SecurityHealth:
    status: str  # healthy | degraded | critical
    trust_score: float
    risk_score: float
    open_incidents: int
    failed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThreatEvent:
    event_id: str
    kind: str
    severity: str
    source: str
    message: str
    at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EnterpriseSecurityCenter:
    """
    Platform-wide Security Center: Zero Trust, identity/authz surfaces,
    AI security, anti-parsing, external AI guard, API/knowledge/secrets,
    monitoring, incident response, compliance readiness.
    """

    VERSION = "32.4"

    def __init__(self, library: SecurityHardeningLibrary | None = None) -> None:
        self.library = library or security_hardening_library
        self.zero_trust = ZeroTrustEngine()
        self.ai = AiSecurityCenter()
        self.anti_parsing = AntiParsingProtection()
        self.external_ai = ExternalAiGuard()
        self.api_policy = ApiGatewayPolicy()
        self.knowledge = KnowledgeSecurity()
        self.audit = AuditCenter(self.library.audit)
        self.incidents = IncidentCenter(self.library.incidents)
        self._timeline: list[ThreatEvent] = []
        self._seq = 0

    def reset(self) -> None:
        self._timeline.clear()
        self._seq = 0
        self.incidents.reset()
        self.anti_parsing.reset()
        self.external_ai.reset()
        self.ai.reset()

    def record_threat(
        self,
        *,
        kind: str,
        severity: str = "medium",
        source: str = "security_center",
        message: str = "",
    ) -> ThreatEvent:
        self._seq += 1
        ev = ThreatEvent(
            event_id=f"thr_{self._seq:06d}",
            kind=kind,
            severity=severity,
            source=source,
            message=message or kind,
        )
        self._timeline.append(ev)
        if severity in {"high", "critical"}:
            self.incidents.open(
                title=f"Threat: {kind}",
                severity=severity,
                source=source,
            )
        return ev

    def verify_request(self, context: dict[str, Any]) -> dict[str, Any]:
        """Zero Trust continuous verification for every request context."""
        zt = self.zero_trust.evaluate_continuous(context)
        if not zt["allowed"]:
            self.record_threat(
                kind="zero_trust_deny",
                severity="high",
                source=str(context.get("path") or "request"),
                message="Zero Trust denied request",
            )
        return zt

    def platform_risk_score(self) -> float:
        """0–100 risk (higher = worse). Derived from trust + open incidents + recent threats."""
        zt = self.zero_trust.evaluate_continuous(
            {
                "user": "platform",
                "device": "platform",
                "token": "platform",
                "ip": "127.0.0.1",
                "context": "platform",
                "risk_level": 0.1,
                "security_policy": "default",
            }
        )
        trust = float(zt.get("trust_score") or 0)
        open_inc = len(self.incidents.list_open())
        recent_high = sum(
            1 for e in self._timeline[-50:] if e.severity in {"high", "critical"}
        )
        risk = round(max(0.0, min(100.0, (1.0 - trust) * 60 + open_inc * 8 + recent_high * 5)), 1)
        return risk

    def health(self) -> SecurityHealth:
        risk = self.platform_risk_score()
        open_inc = len(self.incidents.list_open())
        failed: list[str] = []
        if risk >= 70:
            failed.append("elevated_platform_risk")
        if open_inc >= 3:
            failed.append("multiple_open_incidents")
        if risk >= 85 or open_inc >= 5:
            status = "critical"
        elif risk >= 50 or open_inc >= 1 or failed:
            status = "degraded"
        else:
            status = "healthy"
        trust = round(1.0 - risk / 100.0, 3)
        return SecurityHealth(
            status=status,
            trust_score=trust,
            risk_score=risk,
            open_incidents=open_inc,
            failed_checks=failed,
        )

    def threat_timeline(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._timeline[-limit:]]

    def dashboard(self) -> dict[str, Any]:
        h = self.health()
        return {
            "version": self.VERSION,
            "security_dashboard": True,
            "security_health": h.to_dict(),
            "platform_risk_score": h.risk_score,
            "threat_timeline": self.threat_timeline(limit=20),
            "incident_center": {
                "open": self.incidents.list_open(),
                "emergency_mode": self.incidents.emergency_mode,
            },
            "security_analytics": {
                "ai": self.ai.analytics(),
                "anti_parsing": self.anti_parsing.analytics(),
                "external_ai": self.external_ai.analytics(),
                "api": self.api_policy.analytics(),
            },
            "audit_center": self.audit.summary(),
            "capabilities": self.capabilities(),
            "system_of_record": "platform_security.security_center",
            "identity_adapter": "applications/enterprise_hub/security (ISAM)",
            "http_adapter": "middleware/security_middleware.py",
            "prompt_firewall": "applications/enterprise_hub/ai_provider_hub/prompt_firewall.py",
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "zero_trust": True,
            "identity": [
                "oauth2",
                "oidc",
                "google",
                "jwt_rotation",
                "refresh_tokens",
                "service_accounts",
                "api_keys",
                "mfa",
                "trusted_devices",
                "session_manager",
            ],
            "authorization": [
                "rbac",
                "abac",
                "policy_engine",
                "permission_matrix",
                "org_isolation",
                "tenant_isolation",
                "resource_permissions",
                "context_aware",
            ],
            "ai_security": True,
            "anti_parsing": True,
            "external_ai_protection": True,
            "api_security": True,
            "knowledge_security": True,
            "secrets": True,
            "monitoring": True,
            "incident_response": True,
            "compliance": ["gdpr", "iso27001", "soc2", "audit_export"],
            "no_vertical_security_logic": True,
            "sprint": self.VERSION,
        }


enterprise_security_center = EnterpriseSecurityCenter()
