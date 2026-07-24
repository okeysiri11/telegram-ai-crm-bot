"""Workflow Intelligence library facade — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.ai_builder import AIWorkflowBuilder
from platform_workflow_intelligence.analytics import WorkflowAnalytics
from platform_workflow_intelligence.approvals import HumanApprovalNode
from platform_workflow_intelligence.designer import VisualWorkflowDesigner
from platform_workflow_intelligence.execution import ExecutionEngine
from platform_workflow_intelligence.integrations import WorkflowIntegrations
from platform_workflow_intelligence.library import WorkflowLibrary
from platform_workflow_intelligence.models import PRINCIPLES
from platform_workflow_intelligence.optimization import AIOptimization
from platform_workflow_intelligence.policies import AIExecutionPolicies
from platform_workflow_intelligence.registry import WorkflowRegistry


class WorkflowIntelligenceLibrary:
    def __init__(self) -> None:
        self.registry = WorkflowRegistry()
        self.designer = VisualWorkflowDesigner()
        self.ai_builder = AIWorkflowBuilder()
        self.approvals = HumanApprovalNode()
        self.execution = ExecutionEngine()
        self.analytics = WorkflowAnalytics()
        self.optimization = AIOptimization()
        self.integrations = WorkflowIntegrations()
        self.policies = AIExecutionPolicies()
        self.library = WorkflowLibrary()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        wf = self.library.instantiate(industry="beauty", workflow_id="wf_beauty_boot")
        for ntype in ("decision", "ai_decision", "payment"):
            wf = self.designer.add_node(wf, node_type=ntype)
        wf = self.policies.set_policy(wf, policy="requires_owner")
        approval = self.approvals.require(kind="owner_approval", actor="platform_owner")
        analysis = self.ai_builder.analyze(wf)
        blocked = self.execution.run(workflow=wf, mode="async", owner_approved=False)
        executed = self.execution.run(workflow=wf, mode="async", owner_approved=True)
        runs = [
            {"duration_ms": 1200, "success": True, "cost": 2, "ai_tip": "ok"},
            {"duration_ms": 900, "success": True, "cost": 2},
            {"duration_ms": 1100, "status": "completed", "cost": 1},
        ]
        stats = self.analytics.summarize(runs=runs)
        tips = self.optimization.improve(analytics=stats)
        links = self.integrations.link()
        catalog = self.library.catalog()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "workflow_intelligence_ready": True,
            "visual_designer_ready": True,
            "ai_execution_ready": True,
            "workflow_library_ready": True,
            "drag_drop": True,
            "ai_may_act": False,
            "mutates_workflow": False,
            "owner_decision_required": True,
            "blocked_without_owner": blocked["status"] == "blocked_awaiting_owner",
            "executed_after_owner": executed["executed"],
            "success_rate_95pct": stats["success_rate_95pct"],
            "library_industries": catalog["count"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "workflow": wf,
                "approval": approval,
                "analysis": analysis,
                "blocked": blocked,
                "executed": executed,
                "analytics": stats,
                "optimization": tips,
                "catalog": catalog,
                "palette": self.designer.palette(),
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "designer",
                "ai_builder",
                "approvals",
                "execution",
                "analytics",
                "optimization",
                "policies",
                "library",
            ],
            "principles": self.principles(),
            "palette": self.designer.palette(),
        }


workflow_intelligence_library = WorkflowIntelligenceLibrary()
