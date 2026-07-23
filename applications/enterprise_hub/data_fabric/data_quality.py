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



from applications.enterprise_hub.data_fabric.models import QUALITY_CHECKS


class DataQualityEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assess(self, *, asset_id: str, metrics: dict[str, float] | None = None) -> dict[str, Any]:
        if not asset_id:
            raise ValidationError("asset_id is required")
        defaults = {c: 0.95 for c in QUALITY_CHECKS}
        if metrics:
            defaults.update({k: float(v) for k, v in metrics.items() if k in QUALITY_CHECKS})
        score = sum(defaults.values()) / len(defaults)
        issues = [k for k, v in defaults.items() if v < 0.8]
        qid = _id("edf_qual")
        return self.store.edf_quality.save(
            qid,
            {
                "quality_id": qid,
                "asset_id": asset_id,
                "metrics": defaults,
                "score": round(score, 4),
                "issues": issues,
                "passed": len(issues) == 0,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.edf_quality.list_all()
        return {
            "assessments": len(items),
            "avg_score": (sum(i.get("score", 0) for i in items) / len(items)) if items else 0,
            "failed": sum(1 for i in items if not i.get("passed")),
        }
