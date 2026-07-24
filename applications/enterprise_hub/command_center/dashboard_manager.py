from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.command_center.dashboards import all_blueprints
from applications.enterprise_hub.command_center.models import DASHBOARD_KINDS
from applications.enterprise_hub.command_center.widget_manager import WidgetManager


class DashboardManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.widgets = WidgetManager(self.store)

    def blueprints(self) -> list[dict[str, Any]]:
        return all_blueprints()

    def create(self, *, kind: str, title: str = "", workspace_id: str | None = None) -> dict[str, Any]:
        if kind not in DASHBOARD_KINDS:
            raise ValidationError(f"invalid dashboard kind: {kind}")
        bp = next((b for b in all_blueprints() if b["kind"] == kind), None)
        widget_ids = []
        for wk in (bp or {}).get("default_widgets", ["kpi", "alerts"]):
            w = self.widgets.create(kind=wk, payload={"dashboard": kind})
            widget_ids.append(w["widget_id"])
        did = _id("ecc_dash")
        record = {
            "dashboard_id": did,
            "kind": kind,
            "title": title or (bp or {}).get("title", kind),
            "sections": list((bp or {}).get("sections", [])),
            "widget_ids": widget_ids,
            "workspace_id": workspace_id,
            "created_at": _now(),
        }
        return self.store.ecc_dashboards.save(did, record)

    def get(self, dashboard_id: str) -> dict[str, Any]:
        item = self.store.ecc_dashboards.get(dashboard_id)
        if not item:
            raise NotFoundError(f"dashboard not found: {dashboard_id}")
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ecc_dashboards.list_all()

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        return {
            "dashboards": len(items),
            "by_kind": {k: sum(1 for i in items if i.get("kind") == k) for k in DASHBOARD_KINDS},
        }
