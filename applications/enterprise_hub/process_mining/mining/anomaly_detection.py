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




class AnomalyDetection:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def detect(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        anomalies = []
        for v in process.get("variants") or []:
            share = float(v.get("share_pct") or 0)
            if share < 5 and share > 0:
                anomalies.append({"type": "rare_variant", "path": v.get("path"), "share_pct": share})
            path = v.get("path") or []
            if len(path) != len(set(path)):
                anomalies.append({"type": "loop", "path": path})
        aid = _id("epm_anom")
        return self.store.epm_anomalies.save(
            aid,
            {
                "anomaly_id": aid,
                "process_id": process_id,
                "anomalies": anomalies,
                "count": len(anomalies),
                "at": _now(),
            },
        )
