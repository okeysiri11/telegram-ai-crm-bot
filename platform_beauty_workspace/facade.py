"""Beauty Workspace library facade — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.assistant import AIAssistantPanel
from platform_beauty_workspace.integrations import WorkspaceIntegrations
from platform_beauty_workspace.models import PRINCIPLES
from platform_beauty_workspace.notifications import NotificationCenter
from platform_beauty_workspace.panel import ReceptionPanel
from platform_beauty_workspace.quick_actions import QuickActions
from platform_beauty_workspace.reception import ReceptionDashboard
from platform_beauty_workspace.schedule import LiveSchedule
from platform_beauty_workspace.search import SmartSearch


class BeautyWorkspaceLibrary:
    def __init__(self) -> None:
        self.reception = ReceptionDashboard()
        self.schedule = LiveSchedule()
        self.panel = ReceptionPanel()
        self.search = SmartSearch()
        self.notifications = NotificationCenter()
        self.quick_actions = QuickActions()
        self.assistant = AIAssistantPanel()
        self.integrations = WorkspaceIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        sample_appointments = [
            {
                "appointment_id": "a1",
                "customer_id": "c1",
                "employee_id": "e1",
                "resource_id": "r1",
                "service_id": "s1",
                "start": "2026-07-24T10:00:00Z",
                "end": "2026-07-24T10:45:00Z",
                "status": "confirmed",
            },
            {
                "appointment_id": "a2",
                "customer_id": "c2",
                "employee_id": "e1",
                "resource_id": "r2",
                "service_id": "s2",
                "start": "2026-07-24T11:00:00Z",
                "end": "2026-07-24T12:00:00Z",
                "status": "waiting",
            },
            {
                "appointment_id": "a3",
                "customer_id": "c3",
                "employee_id": "e2",
                "resource_id": "r1",
                "service_id": "s1",
                "start": "2026-07-24T09:00:00Z",
                "end": "2026-07-24T09:45:00Z",
                "status": "cancelled",
            },
        ]
        employees = [{"employee_id": "e1", "name": "Anna"}, {"employee_id": "e2", "name": "Ivy"}]
        dash = self.reception.render(
            appointments=sample_appointments,
            employees=employees,
            open_slots=5,
            advisor_recommendations=["launch_promotion", "winback_customers"],
        )
        schedule = self.schedule.render(view="day", appointments=sample_appointments)
        notes = self.notifications.seed_defaults()
        assistant = self.assistant.render(
            open_slots=["14:00", "16:30"],
            recommendations=["launch_promotion"],
            warnings=["client_late_risk"],
            overloaded_masters=["Anna"],
            churn_risks=["c3"],
            promo_ideas=["weekday_discount"],
        )
        quick = self.quick_actions.run(action="book_in_30s", payload={"customer": "walk_in"})
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "reception_ready": dash["status"] == "ready",
            "schedule_views": schedule["views"],
            "panel_actions": len(self.panel.actions()),
            "quick_actions": len(self.quick_actions.actions()),
            "notifications": len(notes),
            "assistant_proposes_only": assistant["proposes_only"],
            "ai_may_execute": False,
            "realtime": True,
            "min_clicks_ops": True,
            "duplicates_core_logic": False,
            "workspace_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "dashboard": dash,
                "schedule": schedule,
                "assistant": assistant,
                "quick": quick,
                "notifications": notes,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "reception",
                "schedule",
                "panel",
                "search",
                "notifications",
                "quick_actions",
                "assistant",
            ],
            "principles": self.principles(),
        }


beauty_workspace_library = BeautyWorkspaceLibrary()
