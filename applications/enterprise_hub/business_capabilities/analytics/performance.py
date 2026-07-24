
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

from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class PerformanceAnalytics:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def report(self, capability_key: str | None = None) -> dict[str, Any]:
        items = self.registry.list_all()
        if capability_key:
            items = [self.registry.require_key(capability_key)]
        if not items:
            raise ValidationError("no capabilities for performance report")
        rows = []
        for item in items:
            level = int(item.get("maturity_level", 1))
            automation = round(min(1.0, level / 5), 2)
            ai_coverage = round(min(1.0, (level - 1) / 4), 2) if level > 1 else 0.0
            rows.append(
                {
                    "capability_key": item["key"],
                    "performance": round(0.5 + level * 0.1, 2),
                    "cost_index": round(1.2 - level * 0.1, 2),
                    "roi": round(0.1 * level, 2),
                    "automation": automation,
                    "ai_coverage": ai_coverage,
                    "tech_debt": round(max(0.05, 0.5 - level * 0.08), 2),
                    "risk": round(max(0.05, 0.45 - level * 0.07), 2),
                    "efficiency": round(0.4 + level * 0.12, 2),
                }
            )
        rid = _id("ebc_aperf")
        record = {
            "analytics_id": rid,
            "kind": "performance",
            "rows": rows,
            "count": len(rows),
            "reported_at": _now(),
        }
        self.store.ebc_analytics.save(rid, record)
        return record
