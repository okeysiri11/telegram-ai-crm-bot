"""Cross-Tenant Learning — Sprint 24.8."""

from __future__ import annotations

from typing import Any


class CrossTenantLearning:
    def aggregate(self, *, anonymized_signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        signals = list(anonymized_signals or [])
        for s in signals:
            if s.get("pii") or s.get("personal_data"):
                raise ValueError("never transfer personal data between tenants")
            if not s.get("anonymized", False):
                raise ValueError("cross-tenant learning requires anonymized signals only")
        # aggregate by industry/pattern without tenant identity
        by_pattern: dict[str, int] = {}
        for s in signals:
            key = s.get("pattern") or s.get("knowledge_type") or "general"
            by_pattern[key] = by_pattern.get(key, 0) + 1
        return {
            "patterns": [{"pattern": k, "tenants_contributing": v, "anonymized": True} for k, v in by_pattern.items()],
            "pii_transferred": False,
            "anonymized_only": True,
            "count": len(signals),
        }
