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



from applications.enterprise_hub.process_mining.conformance_engine import ConformanceEngine


class ConformanceMining:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.engine = ConformanceEngine(self.store)

    def run(self, *, process_id: str, reference_steps: list[str] | None = None) -> dict[str, Any]:
        return self.engine.check(process_id=process_id, reference_steps=reference_steps)
