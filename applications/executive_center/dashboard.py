"""Executive dashboards, KPIs, real-time metrics, activity feed (Sprint 12.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.executive_center.config import DEFAULT_CONFIG
from applications.executive_center.shared.exceptions import NotFoundError, ValidationError
from applications.executive_center.shared.store import ExecutiveCenterStore, executive_center_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutiveDashboard:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def _probe_apps(self) -> dict[str, Any]:
        apps: dict[str, Any] = {}
        probes = {
            "drone_platform": ("applications.drone_platform", "drone_platform"),
            "marketplace": ("applications.marketplace", "marketplace"),
            "workflow_studio": ("applications.workflow_studio", "workflow_studio"),
            "ai_ecosystem": ("applications.ecosystem", "ai_ecosystem"),
        }
        for key, (mod_name, attr) in probes.items():
            try:
                mod = __import__(mod_name, fromlist=[attr])
                app = getattr(mod, attr)
                h = app.health() if hasattr(app, "health") else {}
                apps[key] = {"status": "online", "version": h.get("application_version", "unknown")}
            except Exception:
                apps[key] = {"status": "unavailable"}
        return apps

    def publish_kpi(self, *, name: str, value: float, unit: str = "", scope: str = "global") -> dict[str, Any]:
        kid = f"kpi_{uuid.uuid4().hex[:10]}"
        row = {"kpi_id": kid, "name": name, "value": value, "unit": unit, "scope": scope, "at": _now()}
        self.store.kpis.save(kid, row)
        return row

    def record_metric(self, *, name: str, value: float, tags: dict[str, Any] | None = None) -> dict[str, Any]:
        mid = f"met_{uuid.uuid4().hex[:10]}"
        row = {"metric_id": mid, "name": name, "value": value, "tags": dict(tags or {}), "at": _now()}
        self.store.metrics.save(mid, row)
        return row

    def activity(self, *, actor: str, action: str, detail: str = "") -> dict[str, Any]:
        aid = f"act_{uuid.uuid4().hex[:10]}"
        row = {"activity_id": aid, "actor": actor, "action": action, "detail": detail, "at": _now()}
        self.store.activity.save(aid, row)
        return row

    def build(self, *, dashboard_type: str = "global", company_id: str = "", project_id: str = "", department_id: str = "") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        did = f"dash_{dashboard_type}_{uuid.uuid4().hex[:8]}"
        apps = self._probe_apps()
        kpis = self.store.kpis.list_all()
        metrics = self.store.metrics.list_all()[-20:]
        feed = self.store.activity.list_all()[-20:]
        board = {
            "dashboard_id": did,
            "type": dashboard_type,
            "company_id": company_id,
            "project_id": project_id,
            "department_id": department_id,
            "applications": apps,
            "executive_kpis": kpis[-10:],
            "realtime_metrics": metrics,
            "activity_feed": list(reversed(feed)),
            "summary": {
                "apps_online": sum(1 for a in apps.values() if a.get("status") == "online"),
                "kpi_count": len(kpis),
                "metric_count": len(self.store.metrics.list_all()),
            },
            "at": _now(),
        }
        self.store.dashboards.save(did, board)
        return board

    def global_dashboard(self) -> dict[str, Any]:
        return self.build(dashboard_type="global")

    def company_dashboard(self, company_id: str) -> dict[str, Any]:
        return self.build(dashboard_type="company", company_id=company_id)

    def project_dashboard(self, project_id: str) -> dict[str, Any]:
        return self.build(dashboard_type="project", project_id=project_id)

    def department_dashboard(self, department_id: str) -> dict[str, Any]:
        return self.build(dashboard_type="department", department_id=department_id)

    def finance_dashboard(self) -> dict[str, Any]:
        board = self.build(dashboard_type="finance")
        board["finance"] = {"revenue_index": 1.0, "cost_index": 0.72, "margin_pct": 0.28}
        return board

    def operations_dashboard(self) -> dict[str, Any]:
        board = self.build(dashboard_type="operations")
        board["operations"] = {"open_workflows": len(self.store.metrics.list_all()), "incidents": 0}
        return board

    def ai_dashboard(self) -> dict[str, Any]:
        board = self.build(dashboard_type="ai")
        board["ai"] = {"agents_active": 6, "sessions": len(self.store.ai_sessions.list_all())}
        return board

    def get(self, dashboard_id: str) -> dict[str, Any]:
        item = self.store.dashboards.get(dashboard_id)
        if item is None:
            raise NotFoundError("dashboard", dashboard_id)
        return item

    def all_dashboards(self) -> dict[str, Any]:
        return {
            "global": self.global_dashboard(),
            "finance": self.finance_dashboard(),
            "operations": self.operations_dashboard(),
            "ai": self.ai_dashboard(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "executive_dashboard": "1.0",
            "dashboards": len(self.store.dashboards.list_all()),
            "kpis": len(self.store.kpis.list_all()),
            "ready": True,
        }


executive_dashboard = ExecutiveDashboard()
