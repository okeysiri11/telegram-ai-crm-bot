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




class PredictionContext:
    """Prepare twin state for Simulation / Decision Intelligence / AI Planning / Forecasting."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def build(self, *, twin_ids: list[str] | None = None, horizon: str = "7d") -> dict[str, Any]:
        twins = self.store.edt_twins.list_all()
        if twin_ids:
            twins = [t for t in twins if t.get("twin_id") in twin_ids]
        active = [t for t in twins if t.get("status") == "active"]
        cid = _id("edt_pred")
        return self.store.edt_predictions.save(
            cid,
            {
                "context_id": cid,
                "horizon": horizon,
                "twin_count": len(twins),
                "active_count": len(active),
                "features": [
                    {
                        "twin_id": t["twin_id"],
                        "type": t.get("twin_type"),
                        "state": t.get("state"),
                        "version": t.get("version"),
                    }
                    for t in active
                ],
                "ready_for": ["simulation", "decision_intelligence", "ai_planning", "forecasting"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.edt_predictions.list_all()
        return {"contexts": len(items), "latest_ready": bool(items)}
