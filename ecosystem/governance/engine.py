# Platform governance engine — facade for policies, compliance, lifecycle, admin, risk.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.config import DEFAULT_CONFIG
from ecosystem.governance.administration.service import AdministrationService, administration_service
from ecosystem.governance.audit.service import AuditService, audit_service
from ecosystem.governance.catalog.service import CatalogService, catalog_service
from ecosystem.governance.compliance.service import ComplianceEngine, compliance_engine
from ecosystem.governance.events import GovernanceActionExecutedEvent
from ecosystem.governance.lifecycle.service import LifecycleService, lifecycle_service
from ecosystem.governance.models import GovernanceAction, GovernanceDomain, LifecycleKind, LifecycleState
from ecosystem.governance.policies.service import PolicyService, policy_service
from ecosystem.governance.risk.service import RiskService, risk_service
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class PlatformGovernanceEngine:
    """Enterprise governance, compliance, lifecycle, and administration."""

    def __init__(
        self,
        store: EcosystemStore | None = None,
        policies: PolicyService | None = None,
        compliance: ComplianceEngine | None = None,
        audit: AuditService | None = None,
        lifecycle: LifecycleService | None = None,
        risk: RiskService | None = None,
        administration: AdministrationService | None = None,
        catalog: CatalogService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.policies = policies or policy_service
        self.compliance = compliance or compliance_engine
        self.audit = audit or audit_service
        self.lifecycle = lifecycle or lifecycle_service
        self.risk = risk or risk_service
        self.administration = administration or administration_service
        self.catalog = catalog or catalog_service

    async def execute_action(
        self,
        action_type: str,
        *,
        domain: GovernanceDomain = GovernanceDomain.PLATFORM,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> GovernanceAction:
        action = GovernanceAction(
            action_type=action_type,
            domain=domain,
            actor=actor,
            details=details or {},
        )
        self._store.governance_actions.save(action.action_id, action)
        self.audit.record(action_type, actor=actor, resource_type="governance_action", resource_id=action.action_id, details=details)
        await publish(
            GovernanceActionExecutedEvent(
                action_id=action.action_id,
                action_type=action_type,
                domain=domain.value,
                actor=actor,
            )
        )
        return action

    async def run_governance_cycle(self) -> dict[str, Any]:
        """AI-integrated governance: continuous audit, risk detection, executive notify, optimization hooks."""
        await self.execute_action("governance_cycle_started", actor="governance_engine")

        apps = list(DEFAULT_CONFIG.registered_applications)
        for app_id in apps:
            existing = [r for r in self.lifecycle.list_records(kind=LifecycleKind.APPLICATION) if r.entity_id == app_id]
            if not existing:
                record = await self.lifecycle.register(LifecycleKind.APPLICATION, app_id, entity_id=app_id, version="2.0.0")
                await self.lifecycle.transition(record.record_id, LifecycleState.ACTIVE)
            self.catalog.register(app_id, entry_type="application", version="2.0.0", owner="ecosystem", tags=["registered"])

        audit_result = await self.compliance.continuous_audit()
        risks = await self.risk.detect_from_compliance()
        self.catalog.sync_from_lifecycle()

        integrations: dict[str, Any] = {"executive": False, "optimization": False, "policy_aware_planning": False}
        if self.administration.is_enabled("executive_governance"):
            try:
                from ecosystem.workforce.executive.service import executive_service
                from ecosystem.workforce.models import ExecutiveRole

                await executive_service.decide(
                    ExecutiveRole.CEO,
                    "Governance cycle completed",
                    rationale=f"Audit passed={audit_result['passed']} failed={audit_result['failed']}",
                )
                integrations["executive"] = True
            except Exception:
                pass

        if self.administration.is_enabled("optimization_hooks"):
            try:
                from ecosystem.optimization.engine import optimization_engine

                await optimization_engine.recommendations.generate(force=False)
                integrations["optimization"] = True
            except Exception:
                pass

        try:
            from ecosystem.workforce.models import PlanHorizon
            from ecosystem.workforce.planning.service import planning_service

            await planning_service.create_plan(
                "Policy-aware governance plan",
                PlanHorizon.WEEKLY,
                [{"item": "Remediate failed compliance", "count": audit_result["failed"]}],
            )
            integrations["policy_aware_planning"] = True
        except Exception:
            pass

        await self.execute_action(
            "governance_cycle_completed",
            actor="governance_engine",
            details={"audit": {"passed": audit_result["passed"], "failed": audit_result["failed"]}, "risks": len(risks)},
        )
        return {
            "audit": audit_result,
            "risks": [r.to_dict() for r in risks],
            "administration": self.administration.platform_overview(),
            "integrations": integrations,
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "governance_layer": DEFAULT_CONFIG.governance_layer,
            "compliance_layer": DEFAULT_CONFIG.compliance_layer,
            "policies": self._store.policies.count(),
            "compliance_checks": self._store.compliance_checks.count(),
            "audit_entries": self._store.audit_entries.count(),
            "lifecycle_records": self._store.lifecycle_records.count(),
            "risks": self._store.risk_items.count(),
            "catalog_entries": self._store.catalog_entries.count(),
            "feature_flags": self._store.feature_flags.count(),
            "licenses": self._store.licenses.count(),
        }


platform_governance = PlatformGovernanceEngine()
