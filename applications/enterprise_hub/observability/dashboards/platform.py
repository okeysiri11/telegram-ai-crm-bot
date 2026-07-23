"""Operations dashboards — platform, infrastructure, AI, integrations, business."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.observability.models import DASHBOARD_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OperationsDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.obs_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types and dt not in DASHBOARD_KINDS:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "platform": {
                "services": self.store.obs_services.count(),
                "health": self.store.obs_health.count(),
                "alerts": self.store.obs_alerts.count(),
                "incidents": self.store.obs_incidents.count(),
            },
            "infrastructure": {
                "metrics": self.store.obs_metrics.count(),
                "collections": self.store.obs_collections.count(),
                "exports": self.store.obs_exports.count(),
            },
            "ai": {
                "ai_logs": sum(
                    1
                    for i in self.store.obs_logs.list_all()
                    if isinstance(i, dict) and i.get("kind") == "ai"
                ),
                "diagnostics": self.store.obs_diagnostics.count(),
            },
            "integrations": {
                "integration_logs": sum(
                    1
                    for i in self.store.obs_logs.list_all()
                    if isinstance(i, dict) and i.get("kind") == "integration"
                ),
                "traces": self.store.obs_traces.count(),
            },
            "business": {
                "active_users_metrics": sum(
                    1
                    for i in self.store.obs_metrics.list_all()
                    if isinstance(i, dict) and i.get("kind") == "active_users"
                ),
                "errors": sum(
                    1
                    for i in self.store.obs_logs.list_all()
                    if isinstance(i, dict) and i.get("kind") == "error"
                ),
            },
        }.get(dt, {})
        did = _id("obs_dash")
        return self.store.obs_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.obs_dashboards.count(), "types": self.types}
