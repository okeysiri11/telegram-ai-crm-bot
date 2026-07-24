
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

from applications.enterprise_hub.business_capabilities.models import MATURITY_LEVELS
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class MaturityEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def assess(self, capability_key: str | None = None) -> dict[str, Any]:
        items = self.registry.list_all()
        if capability_key:
            items = [self.registry.require_key(capability_key)]
        if not items:
            raise ValidationError("no capabilities to assess")
        levels = [int(i.get("maturity_level", 1)) for i in items]
        avg = round(sum(levels) / len(levels), 2)
        labels = dict(MATURITY_LEVELS)
        distribution = {lbl: 0 for _, lbl in MATURITY_LEVELS}
        for lv in levels:
            distribution[labels[lv]] += 1
        mid = _id("ebc_mat")
        record = {
            "assessment_id": mid,
            "capability_key": capability_key,
            "count": len(items),
            "average_maturity": avg,
            "enterprise_level": min(5, max(1, round(avg))),
            "distribution": distribution,
            "gap_to_ai_driven": round(5 - avg, 2),
            "assessed_at": _now(),
        }
        self.store.ebc_maturity.save(mid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"assessments": len(self.store.ebc_maturity.list_all())}
