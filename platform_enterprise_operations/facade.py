"""Enterprise Operations library facade — Sprint 23.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_operations.ai_advisor import AIOperationsAdvisor
from platform_enterprise_operations.dashboard import OperationsDashboard
from platform_enterprise_operations.feedback import FeedbackIntelligence
from platform_enterprise_operations.incidents import IncidentCenter
from platform_enterprise_operations.integrations import OperationsIntegrations
from platform_enterprise_operations.models import PRINCIPLES
from platform_enterprise_operations.owner_command import OwnerCommandCenter
from platform_enterprise_operations.pilot_control import PilotControlCenter
from platform_enterprise_operations.platform_monitoring import PlatformMonitoring
from platform_enterprise_operations.release_manager import ReleaseManagerView
from platform_enterprise_operations.tenant_health import TenantHealthMonitor
from platform_enterprise_operations.usage import UsageAnalytics


class EnterpriseOperationsLibrary:
    def __init__(self) -> None:
        self.dashboard = OperationsDashboard()
        self.tenant_health = TenantHealthMonitor()
        self.platform_monitoring = PlatformMonitoring()
        self.pilot_control = PilotControlCenter()
        self.feedback = FeedbackIntelligence()
        self.usage = UsageAnalytics()
        self.ai_advisor = AIOperationsAdvisor()
        self.release_manager = ReleaseManagerView()
        self.incidents = IncidentCenter()
        self.owner_command = OwnerCommandCenter()
        self.integrations = OperationsIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        companies = [
            {"company_id": "c1", "stage": "pilot", "status": "Active", "new_registration": False},
            {"company_id": "c2", "stage": "onboarding", "status": "Onboarding", "new_registration": True},
            {"company_id": "c3", "stage": "production", "status": "Active", "new_registration": False},
        ]
        dash = self.dashboard.render(
            companies=companies,
            services={"hub": "ok", "api": "ok", "ai": "ok"},
            releases=[{"version": "6.11.0", "note": "pilot_release"}],
            users=42,
            ai_agents=8,
        )
        health = self.tenant_health.score(
            company_id="c1",
            dimensions={"crm": 1, "ai": 0.9, "communications_hub": 1, "commerce": 0.95, "marketing": 0.85},
            errors=[],
            warnings=["low_marketing_usage"],
            performance=0.92,
        )
        mon = self.platform_monitoring.snapshot()
        pilot = self.pilot_control.profile(
            company_id="c1",
            readiness_pct=78,
            staff_trained=True,
            daily_users=12,
            feedback=["booking works"],
            issues=["slow reports"],
            improvements=["faster checkout"],
        )
        fb = self.feedback.collect(role="owner", message="Need better reports", company_id="c1", kind="suggestion")
        usage = self.usage.summarize(
            events=[
                {"feature": "booking", "duration_ms": 800},
                {"feature": "booking", "duration_ms": 900},
                {"feature": "pos", "duration_ms": 1200},
                {"feature": "reports", "duration_ms": 4000, "incomplete": True},
                {"feature": "ai_advisor", "ai_recommendation": "rebook_clients"},
            ]
        )
        advice = self.ai_advisor.daily_report(dashboard=dash, pilots=[pilot], usage=usage, monitoring=mon)
        release = self.release_manager.record(
            version="6.11.0",
            changelog=["operations_center", "pilot_release"],
            migrations=["eoc_stores"],
            test_results={"passed": True, "suite": "19.0-23.0"},
            impact="pilot_ops",
        )
        incident = self.incidents.open(title="Sample latency", severity="low", details="reports slow")
        incident = self.incidents.resolve(incident, investigation="N+1 query", fix="index added")
        approval = self.owner_command.approve(
            action="approve_release",
            actor="platform_owner",
            payload={"version": "6.11.0"},
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "pilot_release": True,
            "operations_center_ready": True,
            "tenant_health_ready": True,
            "owner_command_ready": True,
            "pilot_release_ready": True,
            "feedback_to_epi": fb["routed_to"] == "product_intelligence",
            "ai_may_act": False,
            "requires_owner_approval": True,
            "health_score": health["health_score"],
            "monitoring_ok": mon["all_ok"],
            "company_status_sample": dash["pilot"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "dashboard": dash,
                "tenant_health": health,
                "monitoring": mon,
                "pilot": pilot,
                "feedback": fb,
                "usage": usage,
                "advisor": advice,
                "release": release,
                "incident": incident,
                "approval": approval,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "dashboard",
                "tenant_health",
                "platform_monitoring",
                "pilot_control",
                "feedback",
                "usage",
                "ai_advisor",
                "release_manager",
                "incidents",
                "owner_command",
            ],
            "principles": self.principles(),
            "stage": "pilot_release",
        }


enterprise_operations_library = EnterpriseOperationsLibrary()
