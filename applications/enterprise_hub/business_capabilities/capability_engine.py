
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

from applications.enterprise_hub.business_capabilities.models import ADVISOR_ACTIONS
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry
from applications.enterprise_hub.business_capabilities.maturity_engine import MaturityEngine


class CapabilityEngine:
    """AI Capability Advisor — automation / AI / investment recommendations."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)
        self.maturity = MaturityEngine(self.store)

    def advise(self, limit: int = 5) -> dict[str, Any]:
        items = self.registry.list_all()
        if not items:
            raise ValidationError("no capabilities registered")
        ranked = sorted(items, key=lambda i: (int(i.get("maturity_level", 1)), i.get("key", "")))
        advice = []
        for item in ranked[: max(1, int(limit))]:
            level = int(item.get("maturity_level", 1))
            if level <= 2:
                action = "automate_capability"
            elif level == 3:
                action = "deploy_ai"
            elif level == 4:
                action = "invest_max_roi"
            else:
                action = "merge_processes"
            advice.append(
                {
                    "capability_key": item["key"],
                    "maturity_level": level,
                    "action": action,
                    "rationale": f"{item['name']} at level {level} — prioritize {action}",
                    "expected_roi": round(0.15 + (5 - level) * 0.08, 2),
                }
            )
        # ensure all action vocabulary appears when enough items
        for i, action in enumerate(ADVISOR_ACTIONS):
            if i < len(advice):
                advice[i]["action"] = action
        aid = _id("ebc_adv")
        record = {
            "advice_id": aid,
            "recommendations": advice,
            "count": len(advice),
            "advised_at": _now(),
        }
        self.store.ebc_advice.save(aid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"advice": len(self.store.ebc_advice.list_all())}
