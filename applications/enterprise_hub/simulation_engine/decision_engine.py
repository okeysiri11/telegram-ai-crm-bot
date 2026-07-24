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



from applications.enterprise_hub.simulation_engine.models import DECISION_CRITERIA


class DecisionEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def evaluate(
        self,
        *,
        options: list[dict[str, Any]] | None = None,
        weights: dict[str, float] | None = None,
        context: str = "",
    ) -> dict[str, Any]:
        opts = list(options or [])
        if len(opts) < 2:
            raise ValidationError("at least 2 decision options required")
        w = {c: 1.0 for c in DECISION_CRITERIA}
        if weights:
            w.update({k: float(v) for k, v in weights.items() if k in DECISION_CRITERIA})
        ranked = []
        for i, opt in enumerate(opts):
            scores = {
                "profit": float(opt.get("profit", 50)),
                "cost": 100 - float(opt.get("cost", 50)),  # lower cost better
                "risk": 100 - float(opt.get("risk", 50)),
                "time": 100 - float(opt.get("time", 50)),
                "efficiency": float(opt.get("efficiency", 50)),
                "success_probability": float(opt.get("success_probability", 50)),
            }
            total = sum(scores[c] * w.get(c, 1.0) for c in DECISION_CRITERIA)
            ranked.append(
                {
                    "option_id": opt.get("option_id", f"opt-{i}"),
                    "label": opt.get("label", f"Option {i+1}"),
                    "scores": scores,
                    "weighted_score": round(total, 2),
                }
            )
        ranked.sort(key=lambda x: x["weighted_score"], reverse=True)
        did = _id("esi_dec")
        return self.store.esi_decisions.save(
            did,
            {
                "decision_id": did,
                "context": context,
                "weights": w,
                "ranked": ranked,
                "best_option": ranked[0]["option_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"decisions": len(self.store.esi_decisions.list_all())}
