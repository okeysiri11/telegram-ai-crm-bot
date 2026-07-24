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



from applications.enterprise_hub.process_mining.process_repository import ProcessRepository


class ProcessDiscovery:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.repo = ProcessRepository(self.store)

    def discover(self, *, name: str = "discovered-process") -> dict[str, Any]:
        events = sorted(self.store.epm_normalized.list_all(), key=lambda x: x.get("ts") or "")
        if not events:
            raise ValidationError("no normalized events to discover from")
        cases: dict[str, list[str]] = {}
        for e in events:
            cases.setdefault(e["case_id"], []).append(e["activity"])
        # most common path as main process
        path_counts: dict[tuple[str, ...], int] = {}
        for steps in cases.values():
            key = tuple(steps)
            path_counts[key] = path_counts.get(key, 0) + 1
        main = max(path_counts.items(), key=lambda x: x[1])
        total = sum(path_counts.values())
        variants = [
            {"path": list(path), "count": count, "share_pct": round(100 * count / total, 2)}
            for path, count in sorted(path_counts.items(), key=lambda x: -x[1])
        ]
        process = self.repo.save(name=name, steps=list(main[0]), status="discovered", variants=variants)
        did = _id("epm_disc")
        return self.store.epm_discoveries.save(
            did,
            {
                "discovery_id": did,
                "process_id": process["process_id"],
                "case_count": len(cases),
                "variant_count": len(variants),
                "main_path": list(main[0]),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"discoveries": len(self.store.epm_discoveries.list_all())}
