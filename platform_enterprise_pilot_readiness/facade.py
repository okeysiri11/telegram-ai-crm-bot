"""Pilot Readiness library facade — Sprint 23.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_pilot_readiness.accessibility import AccessibilityAudit
from platform_enterprise_pilot_readiness.empty_states import EmptyStateDesigner
from platform_enterprise_pilot_readiness.feedback_widget import PilotFeedbackWidget
from platform_enterprise_pilot_readiness.first_launch import FirstLaunchExperience
from platform_enterprise_pilot_readiness.integrations import PilotReadinessIntegrations
from platform_enterprise_pilot_readiness.learning import AILearningAssistant
from platform_enterprise_pilot_readiness.models import PRINCIPLES
from platform_enterprise_pilot_readiness.performance import PerformanceAudit
from platform_enterprise_pilot_readiness.pilot_checklist import PilotChecklist
from platform_enterprise_pilot_readiness.ux_audit import UXAuditEngine
from platform_enterprise_pilot_readiness.workflow_opt import WorkflowOptimization


class PilotReadinessLibrary:
    def __init__(self) -> None:
        self.ux_audit = UXAuditEngine()
        self.workflow_opt = WorkflowOptimization()
        self.empty_states = EmptyStateDesigner()
        self.first_launch = FirstLaunchExperience()
        self.learning = AILearningAssistant()
        self.performance = PerformanceAudit()
        self.accessibility = AccessibilityAudit()
        self.pilot_checklist = PilotChecklist()
        self.feedback_widget = PilotFeedbackWidget()
        self.integrations = PilotReadinessIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        ux = self.ux_audit.audit_all()
        flows = self.workflow_opt.optimize_all(
            profiles={
                "client_booking": {"steps": 4, "elapsed_ms": 20000},
                "service_sale": {"steps": 3, "elapsed_ms": 15000},
                "product_sale": {"steps": 3, "elapsed_ms": 12000},
                "certificate_issue": {"steps": 3, "elapsed_ms": 18000},
                "campaign_create": {"steps": 4, "elapsed_ms": 30000},
                "company_registration": {"steps": 5, "elapsed_ms": 40000},
            }
        )
        empty = self.empty_states.design(screen="appointments")
        tour = self.first_launch.tour(user_id="u_pilot", role="admin")
        learn = self.learning.observe(user_id="u_pilot", action="client_search", repeat_count=3)
        perf = self.performance.audit()
        a11y = self.accessibility.check(devices=["mobile", "tablet", "desktop", "large_monitor"], scale=1.25, readability=0.92)
        checklist = self.pilot_checklist.evaluate(
            completed={
                "services_ok": True,
                "ai_active": True,
                "communications_ok": True,
                "backups_enabled": True,
                "monitoring_active": True,
                "security_configured": True,
                "roles_configured": True,
                "licenses_active": True,
            }
        )
        fb = self.feedback_widget.submit(kind="idea", message="Faster booking shortcut", rating=5, feature="booking")
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "pilot_ux_ready": True,
            "workflow_optimized": flows["all_under_60s"],
            "empty_states_ready": True,
            "pilot_checklist_ready": checklist["passed"],
            "core_flows_under_60s": flows["all_under_60s"],
            "no_critical_errors": perf["critical"],
            "self_serve_onboarding": True,
            "auto_feedback_collection": fb["auto_forward"],
            "ai_may_act": False,
            "proposes_only": True,
            "average_ux_score": ux["average_ux_score"],
            "pilot_access_granted": checklist["pilot_access_granted"],
            "duplicates_core_logic": False,
            "polishes_existing": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "ux": ux,
                "workflows": flows,
                "empty": empty,
                "tour": tour,
                "learning": learn,
                "performance": perf,
                "accessibility": a11y,
                "checklist": checklist,
                "feedback": fb,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "ux_audit",
                "workflow_opt",
                "empty_states",
                "first_launch",
                "learning",
                "performance",
                "accessibility",
                "pilot_checklist",
                "feedback_widget",
            ],
            "principles": self.principles(),
            "polishes_existing": True,
        }


pilot_readiness_library = PilotReadinessLibrary()
