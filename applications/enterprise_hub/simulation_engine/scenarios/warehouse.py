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


class WarehouseScenario:
    DOMAIN = "warehouse"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def build(
        self,
        *,
        question: str,
        parameters: dict[str, Any] | None = None,
        kind: str = "what_if",
    ) -> dict[str, Any]:
        from applications.enterprise_hub.simulation_engine.scenario_engine import ScenarioEngine
        return ScenarioEngine(self.store).create(
            domain=self.DOMAIN,
            question=question,
            kind=kind,
            parameters=parameters,
        )
