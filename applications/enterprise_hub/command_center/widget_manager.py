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

from applications.enterprise_hub.command_center.models import WIDGET_KINDS
from applications.enterprise_hub.command_center.widgets import all_blueprints, render_widget


class WidgetManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def catalog(self) -> list[dict[str, Any]]:
        return all_blueprints()

    def create(self, *, kind: str, title: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in WIDGET_KINDS:
            raise ValidationError(f"invalid widget kind: {kind}")
        rendered = render_widget(kind, payload)
        wid = _id("ecc_wgt")
        record = {
            "widget_id": wid,
            "kind": kind,
            "title": title or rendered.get("title", kind),
            "payload": payload or {},
            "rendered": rendered,
            "created_at": _now(),
        }
        return self.store.ecc_widgets.save(wid, record)

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ecc_widgets.list_all()

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        return {"widgets": len(items), "kinds": list(WIDGET_KINDS)}
