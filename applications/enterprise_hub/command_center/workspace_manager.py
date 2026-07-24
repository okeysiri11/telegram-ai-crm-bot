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

class WorkspaceManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(self, *, name: str, owner: str = "executive", layout: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        wid = _id("ecc_ws")
        return self.store.ecc_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "name": name,
                "owner": owner,
                "layout": list(layout or ["executive", "operations"]),
                "created_at": _now(),
            },
        )

    def get(self, workspace_id: str) -> dict[str, Any]:
        item = self.store.ecc_workspaces.get(workspace_id)
        if not item:
            raise NotFoundError(f"workspace not found: {workspace_id}")
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ecc_workspaces.list_all()

    def status(self) -> dict[str, Any]:
        return {"workspaces": len(self.list_all())}
