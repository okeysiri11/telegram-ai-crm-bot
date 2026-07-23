"""UsageAnalytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class UsageAnalytics:
    kind = "usage"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        docs = self.store.ekp_documents.list_all()
        retrievals = self.store.ekp_retrievals.list_all()
        answers = self.store.ekp_answers.list_all()
        aid = _id("ekp_an")
        payload: dict[str, Any] = {
            "analytics_id": aid,
            "kind": self.kind,
            "documents": len(docs),
            "retrievals": len(retrievals),
            "answers": len(answers),
            "at": _now(),
        }
        if self.kind == "usage":
            popular = sorted(docs, key=lambda d: len(d.get("tags") or []), reverse=True)[:5]
            payload["popular_documents"] = [{"document_id": d["document_id"], "title": d["title"]} for d in popular]
        elif self.kind == "quality":
            payload["coverage"] = min(1.0, len(docs) / 10) if docs else 0.0
            payload["unused"] = [d["document_id"] for d in docs if d.get("status") == "archived"]
        else:
            avg = 0.0
            scores = []
            for r in retrievals:
                for h in r.get("hits") or []:
                    scores.append(float(h.get("score", 0) or 0))
            if scores:
                avg = sum(scores) / len(scores)
            payload["avg_relevance"] = avg
            payload["rag_effectiveness"] = min(1.0, avg + 0.2)
        return self.store.ekp_analytics.save(aid, payload)
