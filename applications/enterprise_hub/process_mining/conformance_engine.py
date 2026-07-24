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



from applications.enterprise_hub.process_mining.models import DEFAULT_REFERENCE_STEPS, VIOLATION_KINDS


class ConformanceEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(
        self,
        *,
        process_id: str,
        reference_steps: list[str] | None = None,
        sla_hours: float = 48.0,
    ) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        ref = list(reference_steps or DEFAULT_REFERENCE_STEPS)
        actual_variants = process.get("variants") or [{"path": process.get("steps", [])}]
        violations = []
        for v in actual_variants:
            path = v.get("path") or []
            # skipped
            for step in ref:
                if step not in path:
                    violations.append({"kind": "skipped_step", "step": step, "path": path})
            # extra / bypass
            for step in path:
                if step not in ref:
                    violations.append({"kind": "extra_step", "step": step, "path": path})
            # order check
            ref_idx = {s: i for i, s in enumerate(ref)}
            last = -1
            for step in path:
                if step in ref_idx:
                    if ref_idx[step] < last:
                        violations.append({"kind": "unordered", "step": step, "path": path})
                    last = max(last, ref_idx[step])
            # SLA heuristic: long paths
            if len(path) > len(ref) + 1:
                violations.append({"kind": "sla_breach", "step": path[-1], "path": path, "sla_hours": sla_hours})
        cid = _id("epm_conf")
        return self.store.epm_conformance.save(
            cid,
            {
                "conformance_id": cid,
                "process_id": process_id,
                "reference_steps": ref,
                "violations": violations,
                "violation_count": len(violations),
                "conformance_score": round(max(0.0, 1.0 - 0.08 * len(violations)), 3),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.epm_conformance.list_all()
        return {
            "checks": len(items),
            "violations": sum(i.get("violation_count", 0) for i in items),
        }
