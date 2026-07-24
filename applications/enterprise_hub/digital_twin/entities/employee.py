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


class EmployeeTwin:
    TWIN_TYPE = "employee"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(self, *, name: str, owner: str = "system", state: dict[str, Any] | None = None, access: str = "internal") -> dict[str, Any]:
        from applications.enterprise_hub.digital_twin.twin_registry import TwinRegistry
        return TwinRegistry(self.store).register(
            name=name,
            twin_type=self.TWIN_TYPE,
            owner=owner,
            state=state,
            access=access,
        )
