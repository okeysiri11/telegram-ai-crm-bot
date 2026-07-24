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



from applications.enterprise_hub.process_mining.models import BOTTLENECK_KINDS


class BottleneckDetector:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def detect(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        # activity frequencies across variants
        freq: dict[str, int] = {}
        for v in process.get("variants") or []:
            for step in v.get("path") or []:
                freq[step] = freq.get(step, 0) + int(v.get("count", 1))
        bottlenecks = []
        if freq:
            max_step = max(freq, key=freq.get)
            bottlenecks.append({"kind": "overload", "step": max_step, "score": freq[max_step]})
            # rework: steps appearing more than once in same path
            for v in process.get("variants") or []:
                path = v.get("path") or []
                seen = set()
                for step in path:
                    if step in seen:
                        bottlenecks.append({"kind": "rework", "step": step, "score": int(v.get("count", 1))})
                        break
                    seen.add(step)
            # cycle heuristic
            for v in process.get("variants") or []:
                path = v.get("path") or []
                if len(path) != len(set(path)):
                    bottlenecks.append({"kind": "cycle", "step": path[0] if path else "?", "score": 1})
            bottlenecks.append({"kind": "delay", "step": max_step, "score": round(freq[max_step] * 1.5, 2)})
            bottlenecks.append({"kind": "resource_wait", "step": max_step, "score": freq[max_step]})
        # unique by kind+step
        uniq = {}
        for b in bottlenecks:
            uniq[(b["kind"], b["step"])] = b
        items = list(uniq.values())
        bid = _id("epm_bn")
        return self.store.epm_bottlenecks.save(
            bid,
            {
                "bottleneck_id": bid,
                "process_id": process_id,
                "bottlenecks": items,
                "count": len(items),
                "kinds": list(BOTTLENECK_KINDS),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"detections": len(self.store.epm_bottlenecks.list_all())}
