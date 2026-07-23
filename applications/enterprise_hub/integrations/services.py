"""EIP AI assistant and dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIIntegrationAssistant:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assist(
        self,
        *,
        action: str,
        subject: str,
        detail: str = "",
    ) -> dict[str, Any]:
        act = action.lower().strip()
        allowed = (
            "analyze_api",
            "build_mapping",
            "optimize",
            "detect_errors",
            "create_template",
        )
        if act not in allowed:
            raise ValidationError(f"action must be one of {list(allowed)}")
        if not subject:
            raise ValidationError("subject required")
        aid = _id("eip_ai")
        return self.store.eip_ai_assists.save(
            aid,
            {
                "assist_id": aid,
                "action": act,
                "subject": subject,
                "detail": detail,
                "suggestion": f"{act}:{subject}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"assists": self.store.eip_ai_assists.count()}


class EIPDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.eip_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "monitoring": {
                "snapshots": self.store.eip_monitors.count(),
                "retries": self.store.eip_retries.count(),
                "errors": sum(
                    int(i.get("errors", 0))
                    for i in self.store.eip_monitors.list_all()
                    if isinstance(i, dict)
                ),
            },
            "registry": {
                "integrations": self.store.eip_registry.count(),
                "operations": self.store.eip_manager_ops.count(),
            },
            "sync": {
                "syncs": self.store.eip_syncs.count(),
                "schedules": self.store.eip_schedules.count(),
                "fires": self.store.eip_schedule_fires.count(),
            },
            "connectors": {
                "calls": self.store.eip_connector_calls.count(),
                "adapters": self.store.eip_adapter_calls.count(),
            },
            "analytics": {
                "mappings": self.store.eip_mappings.count(),
                "transforms": self.store.eip_transforms.count(),
                "ai_assists": self.store.eip_ai_assists.count(),
                "security": self.store.eip_security.count(),
            },
        }.get(dt, {})
        did = _id("eip_dash")
        return self.store.eip_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.eip_dashboards.count(), "types": self.types}
