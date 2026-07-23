"""Custom workspace template."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.workspace_manager import WorkspaceManager


class CustomWorkspace:
    kind = "custom"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.workspaces = WorkspaceManager(store or enterprise_hub_store)

    def create(self, *, tenant_id: str, name: str = "Custom Workspace", **settings: Any) -> dict[str, Any]:
        return self.workspaces.create(
            tenant_id=tenant_id, name=name, kind=self.kind, settings=settings or {"modules": []}
        )
