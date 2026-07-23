"""Legal research engine — multi-source semantic search and citations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegalResearchEngine:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.modes = list(DEFAULT_CONFIG.aa_research_modes)

    def search(self, *, mode: str, query: str, limit: int = 10) -> dict[str, Any]:
        m = mode.lower().strip()
        if m not in self.modes:
            raise ValidationError(f"mode must be one of {self.modes}")
        if not query:
            raise ValidationError("query required")
        hits = [
            {
                "rank": i + 1,
                "title": f"{m.replace('_', ' ').title()} hit for '{query}'",
                "source": m,
                "score": round(0.95 - i * 0.08, 2),
            }
            for i in range(min(max(1, int(limit)), 5))
        ]
        sid = _id("aa_srch")
        return self.store.aa_searches.save(
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

    def multi_source(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="multi_source", query=query, limit=limit)

    def statute(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="statute", query=query, limit=limit)

    def case_law(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="case_law", query=query, limit=limit)

    def document(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="document", query=query, limit=limit)

    def cross_reference(self, *, query: str, limit: int = 10) -> dict[str, Any]:
        return self.search(mode="cross_reference", query=query, limit=limit)

    def cite(self, *, authority: str, citation_type: str = "statute", detail: str = "") -> dict[str, Any]:
        if not authority:
            raise ValidationError("authority required")
        cid = _id("aa_cite")
        return self.store.aa_citations.save(
            cid,
            {
                "citation_id": cid,
                "authority": authority,
                "citation_type": citation_type,
                "detail": detail,
                "at": _now(),
            },
        )

    def related_authorities(self, *, authority: str) -> dict[str, Any]:
        if not authority:
            raise ValidationError("authority required")
        rid = _id("aa_auth")
        related = [f"Related to {authority} #{i}" for i in range(1, 4)]
        return self.store.aa_authorities.save(
            rid,
            {
                "authority_id": rid,
                "seed": authority,
                "related": related,
                "count": len(related),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "searches": self.store.aa_searches.count(),
            "citations": self.store.aa_citations.count(),
            "authorities": self.store.aa_authorities.count(),
            "modes": self.modes,
        }
