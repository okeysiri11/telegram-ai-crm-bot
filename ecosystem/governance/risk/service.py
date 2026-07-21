# Risk management — assessment, violations, continuity, DR policies.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.governance.audit.service import AuditService, audit_service
from ecosystem.governance.events import RiskDetectedEvent
from ecosystem.governance.models import RiskCategory, RiskItem, RiskSeverity
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class RiskService:
    def __init__(self, store: EcosystemStore | None = None, audit: AuditService | None = None) -> None:
        self._store = store or ecosystem_store
        self.audit = audit or audit_service

    async def assess(
        self,
        title: str,
        *,
        category: RiskCategory = RiskCategory.OPERATIONAL,
        severity: RiskSeverity = RiskSeverity.MEDIUM,
        description: str = "",
        mitigation: str = "",
        related_policy_id: str = "",
    ) -> RiskItem:
        if not title:
            raise ValidationError("title is required")
        risk = RiskItem(
            title=title,
            category=category,
            severity=severity,
            description=description,
            mitigation=mitigation or self._default_mitigation(category),
            related_policy_id=related_policy_id,
        )
        self._store.risk_items.save(risk.risk_id, risk)
        self.audit.record("risk_detected", resource_type="risk", resource_id=risk.risk_id, details={"severity": severity.value})
        await publish(
            RiskDetectedEvent(
                risk_id=risk.risk_id,
                category=category.value,
                severity=severity.value,
                title=title,
            )
        )
        return risk

    def _default_mitigation(self, category: RiskCategory) -> str:
        defaults = {
            RiskCategory.POLICY: "Remediate policy violation and re-run compliance",
            RiskCategory.SECURITY: "Isolate, rotate credentials, notify security",
            RiskCategory.OPERATIONAL: "Escalate to COO and rebalance workload",
            RiskCategory.BUSINESS: "Executive review and contingency plan",
            RiskCategory.CONTINUITY: "Activate business continuity playbook",
            RiskCategory.DISASTER: "Invoke disaster recovery procedures",
        }
        return defaults.get(category, "Review and mitigate")

    async def detect_from_compliance(self) -> list[RiskItem]:
        from ecosystem.governance.models import ComplianceStatus

        risks = []
        for check in self._store.compliance_checks.list_all():
            if check.status != ComplianceStatus.FAILED:
                continue
            existing = next(
                (r for r in self._store.risk_items.list_all() if r.related_policy_id == check.policy_id and r.status == "open"),
                None,
            )
            if existing:
                continue
            risks.append(
                await self.assess(
                    f"Compliance failure on {check.subject_id}",
                    category=RiskCategory.POLICY,
                    severity=RiskSeverity.HIGH,
                    description="; ".join(check.findings),
                    related_policy_id=check.policy_id,
                )
            )
        return risks

    def continuity_policy(self) -> dict[str, Any]:
        return {
            "rto_minutes": 60,
            "rpo_minutes": 15,
            "failover": "secondary_region",
            "communication_plan": ["notify_executives", "enable_maintenance_mode", "status_page"],
        }

    def disaster_recovery_policy(self) -> dict[str, Any]:
        return {
            "backup_frequency_hours": 6,
            "retention_days": 30,
            "restore_drill_cadence": "quarterly",
            "owners": ["chief_operations_ai", "chief_technology_ai"],
        }

    def resolve(self, risk_id: str) -> RiskItem:
        risk = self.get(risk_id)
        risk.status = "resolved"
        self._store.risk_items.save(risk_id, risk)
        return risk

    def get(self, risk_id: str) -> RiskItem:
        risk = self._store.risk_items.get(risk_id)
        if risk is None:
            raise NotFoundError("RiskItem", risk_id)
        return risk

    def list_risks(self, *, severity: RiskSeverity | None = None, status: str = "") -> list[RiskItem]:
        risks = self._store.risk_items.list_all()
        if severity:
            risks = [r for r in risks if r.severity == severity]
        if status:
            risks = [r for r in risks if r.status == status]
        return sorted(risks, key=lambda r: r.created_at, reverse=True)


risk_service = RiskService()
