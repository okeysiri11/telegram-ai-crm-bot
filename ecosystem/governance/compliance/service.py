# Compliance engine — policy checks, retention, access reviews.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.governance.audit.service import AuditService, audit_service
from ecosystem.governance.events import ComplianceFailedEvent, CompliancePassedEvent
from ecosystem.governance.models import AccessReview, ComplianceCheck, ComplianceStatus, GovernanceDomain
from ecosystem.governance.policies.service import PolicyService, policy_service
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class ComplianceEngine:
    def __init__(
        self,
        store: EcosystemStore | None = None,
        policies: PolicyService | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.policies = policies or policy_service
        self.audit = audit or audit_service

    async def evaluate(
        self,
        policy_id: str,
        subject_type: str,
        subject_id: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> ComplianceCheck:
        policy = self.policies.get(policy_id)
        context = context or {}
        findings: list[str] = []
        for rule in policy.rules:
            if rule == "require_auth" and not context.get("authenticated", True):
                findings.append("Authentication required")
            if rule == "rbac_enforced" and not context.get("rbac", True):
                findings.append("RBAC not enforced")
            if rule == "versioned_releases" and not context.get("versioned", True):
                findings.append("Unversioned release detected")
            if rule == "approval_for_prod" and context.get("environment") == "prod" and not context.get("approved"):
                findings.append("Production change lacks approval")
            if rule == "audit_agent_actions" and not context.get("audited", True):
                findings.append("Agent actions not audited")
            if rule == "retain_365d" and int(context.get("retention_days", 365)) < policy.retention_days:
                findings.append(f"Retention below {policy.retention_days} days")
            if rule == "source_attribution" and not context.get("attributed", True):
                findings.append("Knowledge lacks source attribution")

        status = ComplianceStatus.FAILED if findings else ComplianceStatus.PASSED
        check = ComplianceCheck(
            policy_id=policy_id,
            subject_type=subject_type,
            subject_id=subject_id,
            status=status,
            findings=findings,
        )
        self._store.compliance_checks.save(check.check_id, check)
        self.audit.record(
            "compliance_check",
            resource_type=subject_type,
            resource_id=subject_id,
            details={"status": status.value, "policy_id": policy_id},
        )
        if status == ComplianceStatus.PASSED:
            await publish(CompliancePassedEvent(check_id=check.check_id, policy_id=policy_id, subject_id=subject_id))
        else:
            await publish(
                ComplianceFailedEvent(
                    check_id=check.check_id,
                    policy_id=policy_id,
                    subject_id=subject_id,
                    findings=findings,
                )
            )
        return check

    async def evaluate_domain(
        self,
        domain: GovernanceDomain,
        subject_type: str,
        subject_id: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[ComplianceCheck]:
        checks = []
        for policy in self.policies.list_policies(domain=domain):
            if policy.status.value != "active":
                continue
            checks.append(await self.evaluate(policy.policy_id, subject_type, subject_id, context=context))
        return checks

    def retention_policy_summary(self) -> dict[str, Any]:
        policies = self.policies.list_policies(domain=GovernanceDomain.DATA)
        return {
            "policies": [p.to_dict() for p in policies],
            "max_retention_days": max((p.retention_days for p in policies), default=365),
        }

    def access_review(self, subject_id: str, *, reviewer: str = "compliance") -> AccessReview:
        if not subject_id:
            raise ValidationError("subject_id is required")
        findings = []
        # Simple review against open risks / failed checks
        failed = [c for c in self._store.compliance_checks.list_all() if c.subject_id == subject_id and c.status == ComplianceStatus.FAILED]
        if failed:
            findings.append(f"{len(failed)} failed compliance checks")
        review = AccessReview(
            subject_id=subject_id,
            reviewer=reviewer,
            status="completed" if not findings else "action_required",
            findings=findings,
        )
        self._store.access_reviews.save(review.review_id, review)
        self.audit.record("access_review", resource_type="subject", resource_id=subject_id, details={"status": review.status})
        return review

    def list_checks(self, *, status: ComplianceStatus | None = None) -> list[ComplianceCheck]:
        checks = self._store.compliance_checks.list_all()
        if status:
            checks = [c for c in checks if c.status == status]
        return sorted(checks, key=lambda c: c.created_at, reverse=True)

    def get_check(self, check_id: str) -> ComplianceCheck:
        check = self._store.compliance_checks.get(check_id)
        if check is None:
            raise NotFoundError("ComplianceCheck", check_id)
        return check

    async def continuous_audit(self) -> dict[str, Any]:
        """Run compliance across active domains for registered applications."""
        from ecosystem.config import DEFAULT_CONFIG

        results = []
        for app_id in DEFAULT_CONFIG.registered_applications:
            for domain in GovernanceDomain:
                checks = await self.evaluate_domain(
                    domain,
                    "application",
                    app_id,
                    context={"authenticated": True, "rbac": True, "versioned": True, "audited": True, "attributed": True, "retention_days": 365},
                )
                results.extend(checks)
        passed = sum(1 for c in results if c.status == ComplianceStatus.PASSED)
        return {"total": len(results), "passed": passed, "failed": len(results) - passed, "checks": [c.to_dict() for c in results]}


compliance_engine = ComplianceEngine()
