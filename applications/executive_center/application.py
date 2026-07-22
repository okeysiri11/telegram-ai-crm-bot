# ExecutiveCenterApplication — Executive Command Center (Sprint 12.3).

from __future__ import annotations

from typing import Any

from applications.executive_center.config import DEFAULT_CONFIG, ExecutiveCenterConfig
from applications.executive_center.dashboard import ExecutiveDashboard, executive_dashboard
from applications.executive_center.monitoring import SystemMonitoring, system_monitoring
from applications.executive_center.services import (
    EnterpriseControl,
    ExecutiveAI,
    ExecutiveAnalytics,
    ExecutiveVisualization,
    enterprise_control,
    executive_ai,
    executive_analytics,
    executive_visualization,
)
from applications.executive_center.shared.store import ExecutiveCenterStore, executive_center_store
from applications.executive_center.twins import DigitalTwinEngine, digital_twin_engine


class ExecutiveCenterApplication:
    def __init__(
        self,
        *,
        config: ExecutiveCenterConfig | None = None,
        store: ExecutiveCenterStore | None = None,
        dashboard: ExecutiveDashboard | None = None,
        twins: DigitalTwinEngine | None = None,
        monitoring: SystemMonitoring | None = None,
        ai: ExecutiveAI | None = None,
        analytics: ExecutiveAnalytics | None = None,
        visualization: ExecutiveVisualization | None = None,
        enterprise: EnterpriseControl | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or executive_center_store
        self.dashboard = dashboard or executive_dashboard
        self.twins = twins or digital_twin_engine
        self.monitoring = monitoring or system_monitoring
        self.ai = ai or executive_ai
        self.analytics = analytics or executive_analytics
        self.visualization = visualization or executive_visualization
        self.enterprise = enterprise or enterprise_control

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        twins = self.twins.ensure_ecosystem_twins()
        sample = self.monitoring.sample()
        self.monitoring.health_check(target="api_gateway", ok=True)
        self.monitoring.health_check(target="agents", ok=True)
        board = self.dashboard.global_dashboard()
        self.dashboard.activity(actor="system", action="bootstrap", detail="executive center online")
        return {
            "bootstrap": True,
            "twins_created": len(twins),
            "monitoring_sample": sample["sample_id"],
            "dashboard_id": board["dashboard_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "executive_command_center_ready": True,
            "digital_twin_ready": True,
            "executive_ai_ready": True,
            "enterprise_control_center_ready": True,
            "engines": {
                "executive_dashboard": self.config.executive_dashboard,
                "digital_twin": self.config.digital_twin,
                "system_monitoring": self.config.system_monitoring,
                "executive_ai": self.config.executive_ai,
                "analytics": self.config.analytics,
                "visualization": self.config.visualization,
                "enterprise": self.config.enterprise,
            },
            "dashboard": self.dashboard.status(),
            "twins": self.twins.status(),
            "monitoring": self.monitoring.status(),
            "ai": self.ai.status(),
            "analytics": self.analytics.status(),
            "visualization": self.visualization.status(),
            "enterprise": self.enterprise.status(),
        }


executive_center = ExecutiveCenterApplication()
