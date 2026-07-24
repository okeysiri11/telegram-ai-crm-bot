"""Command Center Suite facade — Sprint 20.12."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.command_center.action_center import ActionCenter
from applications.enterprise_hub.command_center.alert_engine import AlertEngine
from applications.enterprise_hub.command_center.analytics.executive_metrics import ExecutiveMetrics
from applications.enterprise_hub.command_center.analytics.realtime import RealtimeAnalytics
from applications.enterprise_hub.command_center.analytics.trends import TrendsAnalytics
from applications.enterprise_hub.command_center.command_center import (
    AIExecutiveAssistant,
    AISituationRoom,
    EnterpriseHealthMonitor,
    EnterpriseMap,
)
from applications.enterprise_hub.command_center.command_dispatcher import CommandDispatcher
from applications.enterprise_hub.command_center.dashboard_manager import DashboardManager
from applications.enterprise_hub.command_center.executive_dashboard import ExecutiveDashboard
from applications.enterprise_hub.command_center.models import INTEGRATION_TARGETS
from applications.enterprise_hub.command_center.navigation_manager import NavigationManager
from applications.enterprise_hub.command_center.notification_center import NotificationCenter
from applications.enterprise_hub.command_center.realtime_monitor import RealtimeMonitor
from applications.enterprise_hub.command_center.widget_manager import WidgetManager
from applications.enterprise_hub.command_center.workspace_manager import WorkspaceManager
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class CommandCenterSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.widgets = WidgetManager(self.store)
        self.workspaces = WorkspaceManager(self.store)
        self.navigation = NavigationManager(self.store)
        self.dashboards = DashboardManager(self.store)
        self.executive = ExecutiveDashboard(self.store)
        self.health = EnterpriseHealthMonitor(self.store)
        self.situation = AISituationRoom(self.store)
        self.assistant = AIExecutiveAssistant(self.store)
        self.alerts = AlertEngine(self.store)
        self.notifications = NotificationCenter(self.store)
        self.actions = ActionCenter(self.store)
        self.dispatcher = CommandDispatcher(self.store)
        self.realtime = RealtimeMonitor(self.store)
        self.enterprise_map = EnterpriseMap(self.store)
        self.executive_metrics = ExecutiveMetrics(self.store)
        self.realtime_analytics = RealtimeAnalytics(self.store)
        self.trends = TrendsAnalytics(self.store)

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        ws = self.workspaces.create(name="Executive HQ", owner="ceo", layout=["executive", "operations", "ai"])
        nav = self.navigation.tree()
        health = self.health.evaluate()
        exec_dash = self.executive.render(health_score=health["enterprise_health_score"], workspace_id=ws["workspace_id"])
        ops = self.dashboards.create(kind="operations", workspace_id=ws["workspace_id"])
        for kind in ("finance", "maritime", "ai", "security"):
            self.dashboards.create(kind=kind, workspace_id=ws["workspace_id"])
        sit = self.situation.brief()
        asst = self.assistant.assist(prompt="Prepare daily executive brief")
        self.alerts.raise_alert(kind="sla_breach", severity="warning", message="Logistics SLA within 5%")
        self.alerts.raise_alert(kind="ai_recommendation", severity="info", message="Automate customs checks")
        self.alerts.raise_alert(kind="critical_event", severity="critical", message="Berth crane offline 12m")
        act = self.actions.dispatch(kind="run_simulation", payload={"scenario": "berth_optimize"})
        cmd = self.dispatcher.dispatch_command(command="Start workflow for incident response")
        rt = self.realtime.snapshot()
        emap = self.enterprise_map.render()
        metrics = self.executive_metrics.report()
        trends = self.trends.report()
        return {
            "bootstrap": True,
            "workspace_id": ws["workspace_id"],
            "navigation_id": nav["navigation_id"],
            "health_id": health["health_id"],
            "enterprise_health_score": health["enterprise_health_score"],
            "executive_id": exec_dash["executive_id"],
            "operations_dashboard_id": ops["dashboard_id"],
            "situation_id": sit["situation_id"],
            "daily_brief": sit["daily_brief"],
            "assistant_id": asst["assistant_id"],
            "alerts_open": self.alerts.status()["open"],
            "action_id": act["action_id"],
            "command_id": cmd["command_id"],
            "realtime_id": rt["monitor_id"],
            "map_id": emap["map_id"],
            "map_entities": emap["entity_count"],
            "metrics_id": metrics["analytics_id"],
            "trends_id": trends["analytics_id"],
            "dashboards": self.dashboards.status()["dashboards"],
            "integrations": self.integrations(),
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "workspaces": self.workspaces.status(),
            "dashboards": self.dashboards.status(),
            "widgets": self.widgets.status(),
            "navigation": self.navigation.status(),
            "alerts": self.alerts.status(),
            "actions": self.actions.status(),
            "realtime": self.realtime.status(),
            "notifications": self.notifications.status(),
            "commands": self.dispatcher.status(),
        }


command_center = CommandCenterSuite()
