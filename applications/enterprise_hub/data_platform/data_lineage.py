"""Data lineage — provenance across sources, processes, agents, integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataLineage:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(
        self,
        *,
        entity_id: str,
        source: str,
        actor: str = "system",
        process: str = "",
        ai_agent: str = "",
        integration: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        if not entity_id or not source:
            raise ValidationError("entity_id and source required")
        lid = _id("edp_lin")
        return self.store.edp_lineage.save(
            lid,
            {
                "lineage_id": lid,
                "entity_id": entity_id,
                "source": source,
                "actor": actor,
                "process": process,
                "ai_agent": ai_agent,
                "integration": integration,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.edp_lineage.count()}
