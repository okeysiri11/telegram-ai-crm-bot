"""Judicial search — semantic, decision/case/judge/court/participant/article."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


SEARCH_MODES = (
    "semantic",
    "decision_number",
    "case_number",
    "judge",
    "court",
    "participant",
    "article",
    "keyword",
    "similar",
)


class JudicialSearch:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def search(self, *, mode: str, query: str, limit: int = 10) -> dict[str, Any]:
        m = mode.lower().strip()
        if m not in SEARCH_MODES:
            raise ValidationError(f"mode must be one of {list(SEARCH_MODES)}")
        if not query:
            raise ValidationError("query required")
        hits = self._match(query=query, mode=m, limit=max(1, int(limit)))
        sid = _id("ji_srch")
        return self.store.ji_searches.save(
            sid,
            {
                "search_id": sid,
                "mode": m,
                "query": query,
                "hits": hits,
                "hit_count": len(hits),
                "at": _now(),
            },
        )

    def semantic(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="semantic", query=query, limit=limit)

    def decision_number(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="decision_number", query=query, limit=limit)

    def case_number(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="case_number", query=query, limit=limit)

    def judge(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="judge", query=query, limit=limit)

    def court(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="court", query=query, limit=limit)

    def participant(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="participant", query=query, limit=limit)

    def article(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="article", query=query, limit=limit)

    def keyword(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="keyword", query=query, limit=limit)

    def similar(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="similar", query=query, limit=limit)

    def _match(self, *, query: str, mode: str, limit: int) -> list[dict[str, Any]]:
        q = query.lower()
        scored: list[dict[str, Any]] = []
        for doc in self.store.ji_decisions.list_all():
            score = 0.0
            if mode == "decision_number" and q in str(doc.get("decision_number", "")).lower():
                score = 1.0
            elif mode == "case_number" and q in str(doc.get("case_number", "")).lower():
                score = 1.0
            elif mode == "judge" and q in str(doc.get("judge_name", "")).lower():
                score = 0.95
            elif mode == "court" and q in str(doc.get("court_name", "")).lower():
                score = 0.95
            elif mode == "participant":
                parts = " ".join(doc.get("participants") or []).lower()
                score = 0.9 if q in parts else 0.0
            elif mode == "article":
                arts = " ".join(doc.get("articles") or []).lower()
                score = 0.9 if q in arts else 0.0
            else:
                text = (
                    f"{doc.get('title', '')} {doc.get('summary', '')} {doc.get('body', '')} "
                    f"{doc.get('outcome', '')}"
                ).lower()
                if q in text:
                    score = 0.85 if mode in ("keyword", "semantic", "similar") else 0.5
                elif any(tok in text for tok in q.split() if len(tok) > 2):
                    score = 0.55 if mode in ("semantic", "similar") else 0.35
            if score > 0:
                scored.append(
                    {
                        "decision_id": doc.get("decision_id"),
                        "title": doc.get("title"),
                        "decision_type": doc.get("decision_type"),
                        "score": round(score, 3),
                        "mode": mode,
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def status(self) -> dict[str, Any]:
        return {"searches": self.store.ji_searches.count(), "modes": list(SEARCH_MODES)}
