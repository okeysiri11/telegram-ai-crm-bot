"""Legislation repositories — constitution, codes, laws, regulations, treaties."""

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


REPO_TYPES = [
    "constitution",
    "code",
    "law",
    "regulation",
    "government_resolution",
    "ministerial_order",
    "international_treaty",
    "local_regulation",
]

_TYPE_STORE = {
    "constitution": "li_constitutions",
    "code": "li_codes",
    "law": "li_laws",
    "regulation": "li_regulations",
    "government_resolution": "li_resolutions",
    "ministerial_order": "li_orders",
    "international_treaty": "li_treaties",
    "local_regulation": "li_local_regs",
}


class LegislationRepository:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.li_repository_types)

    def _bucket(self, repo_type: str) -> Any:
        attr = _TYPE_STORE.get(repo_type)
        if attr is None:
            raise ValidationError(f"repo_type must be one of {self.types}")
        return getattr(self.store, attr)

    def ingest(
        self,
        *,
        repo_type: str,
        title: str,
        code: str = "",
        jurisdiction: str = "",
        authority: str = "",
        effective_on: str = "",
        body: str = "",
        articles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        rt = repo_type.lower().strip()
        bucket = self._bucket(rt)
        rid = _id(f"li_{rt[:4]}")
        article_rows = articles or []
        record = {
            "document_id": rid,
            "repo_type": rt,
            "title": title,
            "code": code,
            "jurisdiction": jurisdiction,
            "authority": authority,
            "effective_on": effective_on,
            "body": body,
            "articles": article_rows,
            "article_count": len(article_rows),
            "status": "active",
            "created_at": _now(),
        }
        bucket.save(rid, record)
        for idx, art in enumerate(article_rows, start=1):
            aid = _id("li_art")
            self.store.li_articles.save(
                aid,
                {
                    "article_id": aid,
                    "document_id": rid,
                    "number": art.get("number", str(idx)),
                    "title": art.get("title", ""),
                    "text": art.get("text", ""),
                    "at": _now(),
                },
            )
        return record

    def ingest_constitution(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="constitution", **kwargs)

    def ingest_code(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="code", **kwargs)

    def ingest_law(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="law", **kwargs)

    def ingest_regulation(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="regulation", **kwargs)

    def ingest_government_resolution(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="government_resolution", **kwargs)

    def ingest_ministerial_order(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="ministerial_order", **kwargs)

    def ingest_treaty(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="international_treaty", **kwargs)

    def ingest_local_regulation(self, **kwargs: Any) -> dict[str, Any]:
        return self.ingest(repo_type="local_regulation", **kwargs)

    def status(self) -> dict[str, Any]:
        return {
            "constitutions": self.store.li_constitutions.count(),
            "codes": self.store.li_codes.count(),
            "laws": self.store.li_laws.count(),
            "regulations": self.store.li_regulations.count(),
            "resolutions": self.store.li_resolutions.count(),
            "orders": self.store.li_orders.count(),
            "treaties": self.store.li_treaties.count(),
            "local_regulations": self.store.li_local_regs.count(),
            "articles": self.store.li_articles.count(),
        }
