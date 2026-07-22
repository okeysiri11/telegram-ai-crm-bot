"""Enterprise Knowledge — wiki and centers (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.config import DEFAULT_CONFIG
from applications.enterprise.shared.exceptions import ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseKnowledge:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store
        self.centers = list(DEFAULT_CONFIG.knowledge_centers)

    def publish_page(self, *, center: str, title: str, body: str = "") -> dict[str, Any]:
        if center not in self.centers:
            raise ValidationError(f"center must be one of {self.centers}")
        if not title:
            raise ValidationError("title required")
        pid = _id("wiki")
        page = {
            "page_id": pid,
            "center": center,
            "title": title,
            "body": body,
            "published_at": _now(),
        }
        return self.store.wiki_pages.save(pid, page)

    def list_pages(self, center: str | None = None) -> list[dict[str, Any]]:
        pages = self.store.wiki_pages.list_all()
        if center:
            return [p for p in pages if p.get("center") == center]
        return pages

    def bootstrap_centers(self) -> list[dict[str, Any]]:
        pages = []
        for center in self.centers:
            pages.append(
                self.publish_page(
                    center=center,
                    title=f"{center.replace('_', ' ').title()} Center",
                    body=f"Enterprise {center} knowledge hub.",
                )
            )
        return pages

    def status(self) -> dict[str, Any]:
        return {
            "pages": len(self.store.wiki_pages.list_all()),
            "centers": self.centers,
        }


enterprise_knowledge = EnterpriseKnowledge()
