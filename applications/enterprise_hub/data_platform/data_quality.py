"""Data quality engine — duplicates, nulls, formats, staleness, rules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.data_platform.models import QUALITY_CHECKS
from applications.enterprise_hub.data_platform.validation import (
    ConsistencyChecker,
    DuplicateDetector,
    Normalizer,
    RuleEngine,
)
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataQuality:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.duplicates = DuplicateDetector(self.store)
        self.consistency = ConsistencyChecker(self.store)
        self.normalizer = Normalizer(self.store)
        self.rules = RuleEngine(self.store)

    def run(self, *, entity_type: str = "") -> dict[str, Any]:
        dup = self.duplicates.detect(entity_type=entity_type)
        cons = self.consistency.check()
        nulls = [
            e["entity_id"]
            for e in self.store.edp_entities.list_all()
            if isinstance(e, dict)
            and (not entity_type or e.get("entity_type") == entity_type.lower())
            and not e.get("name")
        ]
        qid = _id("edp_qual")
        score = 1.0
        if dup["count"] or not cons["ok"] or nulls:
            score = max(0.0, 1.0 - 0.1 * (dup["count"] + len(nulls) + len(cons["issues"])))
        return self.store.edp_quality.save(
            qid,
            {
                "quality_id": qid,
                "entity_type": entity_type.lower(),
                "duplicate_id": dup["detection_id"],
                "consistency_id": cons["check_id"],
                "null_entity_ids": nulls,
                "score": score,
                "checks": list(QUALITY_CHECKS),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "runs": self.store.edp_quality.count(),
            "duplicates": self.duplicates.status(),
            "consistency": self.consistency.status(),
            "normalizer": self.normalizer.status(),
            "rules": self.rules.status(),
        }
