"""AI Legal Search — semantic, NL, article, keyword, citation."""

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
    "natural_language",
    "article",
    "keyword",
    "cross_reference",
    "citation",
    "related",
)


class AILegalSearch:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def search(
        self,
        *,
        mode: str,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        m = mode.lower().strip()
        if m not in SEARCH_MODES:
            raise ValidationError(f"mode must be one of {list(SEARCH_MODES)}")
        if not query:
            raise ValidationError("query required")
        hits = self._match(query=query, mode=m, limit=max(1, int(limit)))
        sid = _id("li_srch")
        return self.store.li_searches.save(
            sid,
            {
                "search_id": sid,
                "mode": m,
                "query": query,
                "filters": filters or {},
                "hits": hits,
                "hit_count": len(hits),
                "at": _now(),
            },
        )

    def semantic(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="semantic", query=query, limit=limit)

    def natural_language(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="natural_language", query=query, limit=limit)

    def article(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="article", query=query, limit=limit)

    def keyword(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="keyword", query=query, limit=limit)

    def cross_reference(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="cross_reference", query=query, limit=limit)

    def citation(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="citation", query=query, limit=limit)

    def related(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="related", query=query, limit=limit)

    def _match(self, *, query: str, mode: str, limit: int) -> list[dict[str, Any]]:
        q = query.lower()
        corpus: list[dict[str, Any]] = []
        for bucket in (
            self.store.li_constitutions,
            self.store.li_codes,
            self.store.li_laws,
            self.store.li_regulations,
            self.store.li_resolutions,
            self.store.li_orders,
            self.store.li_treaties,
            self.store.li_local_regs,
        ):
            corpus.extend(bucket.list_all())
        scored: list[dict[str, Any]] = []
        for doc in corpus:
            text = f"{doc.get('title', '')} {doc.get('code', '')} {doc.get('body', '')}".lower()
            score = 0.0
            if q in text:
                score = 0.9 if mode in ("keyword", "article") else 0.75
            elif any(tok in text for tok in q.split() if len(tok) > 2):
                score = 0.55 if mode in ("semantic", "natural_language", "related") else 0.4
            else:
                score = 0.2 if mode in ("semantic", "natural_language") else 0.0
            if score > 0:
                scored.append(
                    {
                        "document_id": doc.get("document_id"),
                        "title": doc.get("title"),
                        "repo_type": doc.get("repo_type"),
                        "score": round(score, 3),
                        "mode": mode,
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def status(self) -> dict[str, Any]:
        return {"searches": self.store.li_searches.count(), "modes": list(SEARCH_MODES)}
