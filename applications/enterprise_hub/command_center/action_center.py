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

from applications.enterprise_hub.command_center.models import ACTION_KINDS


class ActionCenter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def dispatch(
        self,
        *,
        kind: str,
        payload: dict[str, Any] | None = None,
        actor: str = "executive",
    ) -> dict[str, Any]:
        if kind not in ACTION_KINDS:
            raise ValidationError(f"invalid action kind: {kind}")
        aid = _id("ecc_act")
        return self.store.ecc_actions.save(
            aid,
            {
                "action_id": aid,
                "kind": kind,
                "payload": payload or {},
                "actor": actor,
                "status": "accepted",
                "dispatched_at": _now(),
            },
        )

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ecc_actions.list_all()

    def status(self) -> dict[str, Any]:
        return {"actions": len(self.list_all()), "kinds": list(ACTION_KINDS)}
