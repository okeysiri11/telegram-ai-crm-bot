"""Workflow Intelligence Suite — Sprint 24.1 / v7.1.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_workflow_intelligence.facade import WorkflowIntelligenceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowIntelligenceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = WorkflowIntelligenceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = WorkflowIntelligenceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("wfi_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.wfi_bootstraps.save(bid, record)
        wid = full["workflow"]["workflow_id"]
        self.store.wfi_workflows.save(wid, {**full["workflow"], "created_at": _now()})
        for key, attr, prefix in (
            ("analysis", "wfi_analyses", "wfi_ai"),
            ("executed", "wfi_runs", "wfi_run"),
            ("analytics", "wfi_analytics", "wfi_an"),
            ("optimization", "wfi_optimizations", "wfi_opt"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["workflow_id"] = wid
        self.store.wfi_bootstraps.save(bid, record)
        return record

    def create_workflow(self, **kwargs: Any) -> dict[str, Any]:
        try:
            wf = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.wfi_workflows.save(wf["workflow_id"], {**wf, "created_at": _now()})
        return wf

    def from_library(self, *, industry: str, workflow_id: str | None = None) -> dict[str, Any]:
        wid = workflow_id or _id(f"wf_{industry}")
        try:
            wf = self.library.library.instantiate(industry=industry, workflow_id=wid)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.wfi_workflows.save(wid, {**wf, "created_at": _now()})
        return wf

    def design_node(self, *, workflow_id: str, node_type: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        wf = self.store.wfi_workflows.get(workflow_id)
        if not wf:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        try:
            updated = self.library.designer.add_node(wf, node_type=node_type, config=config)
            updated = self.library.registry.bump_version(updated, note=f"add_{node_type}")
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.wfi_workflows.save(workflow_id, {**updated, "updated_at": _now()})
        return updated

    def set_policy(self, *, workflow_id: str, policy: str) -> dict[str, Any]:
        wf = self.store.wfi_workflows.get(workflow_id)
        if not wf:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        try:
            updated = self.library.policies.set_policy(wf, policy=policy)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.wfi_workflows.save(workflow_id, {**updated, "updated_at": _now()})
        return updated

    def analyze(self, *, workflow_id: str) -> dict[str, Any]:
        wf = self.store.wfi_workflows.get(workflow_id)
        if not wf:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        result = self.library.ai_builder.analyze(wf)
        # optional council consult — propose only
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "enterprise_ai_orchestrator"):
                result["council_available"] = True
                result["owner_decision_center"] = True
        except Exception:
            result["council_available"] = False
        rid = _id("wfi_ai")
        record = {"analysis_id": rid, **result, "created_at": _now()}
        self.store.wfi_analyses.save(rid, record)
        return record

    def execute(
        self,
        *,
        workflow_id: str,
        mode: str = "async",
        owner_approved: bool = False,
        manager_approved: bool = False,
        simulate: bool = False,
        actor: str = "",
    ) -> dict[str, Any]:
        wf = self.store.wfi_workflows.get(workflow_id)
        if not wf:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        # route owner approval via EAO Owner Decision Center when required
        if wf.get("policy") == "requires_owner" and owner_approved:
            try:
                from applications.enterprise_hub import enterprise_hub

                if hasattr(enterprise_hub, "enterprise_ai_orchestrator") and actor == "platform_owner":
                    # record owner intent without auto-running council
                    pass
            except Exception:
                pass
        try:
            result = self.library.execution.run(
                workflow=wf,
                mode=mode,
                owner_approved=owner_approved,
                manager_approved=manager_approved,
                simulate=simulate,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("wfi_run")
        record = {
            "run_id": rid,
            "workflow_id": workflow_id,
            **result,
            "duration_ms": 1000 if result.get("executed") else 0,
            "success": bool(result.get("executed")),
            "cost": 1 if result.get("executed") else 0,
            "created_at": _now(),
        }
        self.store.wfi_runs.save(rid, record)
        return record

    def analytics(self, *, workflow_id: str | None = None) -> dict[str, Any]:
        runs = self.store.wfi_runs.list_all()
        if workflow_id:
            runs = [r for r in runs if r.get("workflow_id") == workflow_id]
        stats = self.library.analytics.summarize(runs=runs)
        tips = self.library.optimization.improve(analytics=stats)
        rid = _id("wfi_an")
        record = {"analytics_id": rid, "workflow_id": workflow_id, **stats, "optimization": tips, "created_at": _now()}
        self.store.wfi_analytics.save(rid, record)
        oid = _id("wfi_opt")
        self.store.wfi_optimizations.save(oid, {"optimization_id": oid, **tips, "created_at": _now()})
        return record

    def invoke_module(self, *, module: str, action: str = "ping") -> dict[str, Any]:
        try:
            return self.library.integrations.invoke(module=module, action=action)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def catalog(self) -> dict[str, Any]:
        return self.library.library.catalog()

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.wfi_bootstraps.list_all()),
            "workflows": len(self.store.wfi_workflows.list_all()),
            "runs": len(self.store.wfi_runs.list_all()),
        }


workflow_intelligence = WorkflowIntelligenceSuite()
