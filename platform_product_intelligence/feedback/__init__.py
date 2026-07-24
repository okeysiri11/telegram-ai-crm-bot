"""Feedback collector — Sprint 22.0."""

from __future__ import annotations

from typing import Any
import hashlib

from platform_product_intelligence.models import FEEDBACK_SOURCES


class FeedbackCollector:
    def normalize(
        self,
        *,
        source: str,
        title: str,
        description: str = "",
        module: str = "enterprise_hub",
        severity: str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if source not in FEEDBACK_SOURCES:
            raise ValueError(f"unknown feedback source: {source}")
        if not title or not str(title).strip():
            raise ValueError("title is required")
        # Cluster by title+module across sources so duplicate signals merge.
        fingerprint = hashlib.sha256(f"{title.strip().lower()}:{module}".encode()).hexdigest()[:16]
        return {
            "source": source,
            "title": title.strip(),
            "description": description or title.strip(),
            "module": module,
            "severity": severity,
            "fingerprint": fingerprint,
            "metadata": dict(metadata or {}),
            "normalized": True,
        }

    def sources(self) -> list[str]:
        return list(FEEDBACK_SOURCES)
