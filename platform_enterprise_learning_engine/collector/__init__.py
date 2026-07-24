"""Knowledge Collector — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import COLLECTOR_SOURCES


class KnowledgeCollector:
    def collect(self, *, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        events = list(events or [])
        accepted = []
        rejected = []
        for event in events:
            source = (event.get("source") or "").lower()
            if source not in COLLECTOR_SOURCES:
                rejected.append({"event": event, "reason": "unknown_source"})
                continue
            if not event.get("confirmed"):
                rejected.append({"event": event, "reason": "unconfirmed"})
                continue
            accepted.append({**event, "source": source, "anonymized": True})
        return {
            "sources": list(COLLECTOR_SOURCES),
            "accepted": accepted,
            "rejected": rejected,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "confirmed_only": True,
        }
