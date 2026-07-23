"""Integration Manager — register, start, stop, update, monitor, journal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.integrations.integration_registry import IntegrationRegistry
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationManager:
    def __init__(
        self,
        store: EnterpriseHubStore | None = None,
        *,
        registry: IntegrationRegistry | None = None,
    ) -> None:
        self.store = store or enterprise_hub_store
        self.registry = registry or IntegrationRegistry(self.store)

    def register(self, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(**kwargs)

    def start(self, *, integration_id: str) -> dict[str, Any]:
        item = self.registry.update_status(integration_id=integration_id, status="running")
        mid = _id("eip_mgr")
        return self.store.eip_manager_ops.save(
            mid,
            {
                "op_id": mid,
                "integration_id": integration_id,
                "operation": "start",
                "status": item["status"],
                "at": _now(),
            },
        )

    def stop(self, *, integration_id: str) -> dict[str, Any]:
        item = self.registry.update_status(integration_id=integration_id, status="stopped")
        mid = _id("eip_mgr")
        return self.store.eip_manager_ops.save(
            mid,
            {
                "op_id": mid,
                "integration_id": integration_id,
                "operation": "stop",
                "status": item["status"],
                "at": _now(),
            },
        )

    def update(
        self,
        *,
        integration_id: str,
        version: str = "",
        connection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        item = self.registry.get(integration_id=integration_id)
        self.registry.update_status(integration_id=integration_id, status="updating")
        if version:
            item["version"] = version
        if connection is not None:
            item["connection"] = connection
        item["change_log"] = list(item.get("change_log") or []) + [
            {"action": "update", "at": _now()}
        ]
        item["status"] = "running"
        item["at"] = _now()
        self.store.eip_registry.save(integration_id, item)
        mid = _id("eip_mgr")
        return self.store.eip_manager_ops.save(
            mid,
            {
                "op_id": mid,
                "integration_id": integration_id,
                "operation": "update",
                "status": item["status"],
                "at": _now(),
            },
        )

    def journal(self, *, integration_id: str, detail: str = "") -> dict[str, Any]:
        if self.store.eip_registry.get(integration_id) is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        if not detail:
            raise ValidationError("detail required")
        jid = _id("eip_log")
        return self.store.eip_journals.save(
            jid,
            {
                "journal_id": jid,
                "integration_id": integration_id,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "operations": self.store.eip_manager_ops.count(),
            "journals": self.store.eip_journals.count(),
            "registry": self.registry.status(),
        }
