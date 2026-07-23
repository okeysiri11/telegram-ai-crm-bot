"""Metrics platform — CPU, RAM, disk, network, DB, queue, API, AI, users."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import METRIC_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MetricsPlatform:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(self, *, kind: str, value: float, labels: dict[str, Any] | None = None) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in METRIC_KINDS:
            raise ValidationError(f"kind must be one of {list(METRIC_KINDS)}")
        mid = _id("obs_met")
        return self.store.obs_metrics.save(
            mid,
            {
                "metric_id": mid,
                "kind": k,
                "value": float(value),
                "labels": labels or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"metrics": self.store.obs_metrics.count(), "kinds": list(METRIC_KINDS)}
