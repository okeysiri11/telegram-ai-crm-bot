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




class VariantMining:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        variants = process.get("variants") or []
        total = sum(int(v.get("count", 1)) for v in variants) or 1
        labeled = []
        for i, v in enumerate(variants):
            share = round(100 * int(v.get("count", 1)) / total, 2)
            label = "standard" if i == 0 else ("accelerated" if share >= 8 else "nonstandard")
            labeled.append({**v, "label": label, "share_pct": share})
        vid = _id("epm_var")
        return self.store.epm_variant_analyses.save(
            vid,
            {
                "analysis_id": vid,
                "process_id": process_id,
                "variants": labeled,
                "variant_count": len(labeled),
                "at": _now(),
            },
        )
