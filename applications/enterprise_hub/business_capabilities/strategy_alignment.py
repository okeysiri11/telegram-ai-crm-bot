
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


class StrategyAlignment:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def align(
        self,
        *,
        capability_key: str,
        strategy: str,
        goals: list[str] | None = None,
        okrs: list[str] | None = None,
        kpis: list[str] | None = None,
        projects: list[str] | None = None,
        investments: list[str] | None = None,
    ) -> dict[str, Any]:
        cap = self.registry.require_key(capability_key)
        if not strategy:
            raise ValidationError("strategy is required")
        aid = _id("ebc_align")
        impact = round(0.4 + 0.1 * int(cap.get("maturity_level", 1)), 2)
        return self.store.ebc_alignments.save(
            aid,
            {
                "alignment_id": aid,
                "capability_id": cap["capability_id"],
                "capability_key": capability_key,
                "strategy": strategy,
                "goals": list(goals or [cap.get("strategic_goal")]),
                "okrs": list(okrs or [f"OKR-{capability_key}"]),
                "kpis": list(kpis or cap.get("kpi") or []),
                "projects": list(projects or []),
                "investments": list(investments or []),
                "strategy_impact_score": impact,
                "aligned_at": _now(),
            },
        )

    def for_capability(self, capability_key: str) -> list[dict[str, Any]]:
        return [a for a in self.store.ebc_alignments.list_all() if a.get("capability_key") == capability_key]

    def status(self) -> dict[str, Any]:
        return {"alignments": len(self.store.ebc_alignments.list_all())}
