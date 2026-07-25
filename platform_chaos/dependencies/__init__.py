"""Dependency Analyzer — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import DEPENDENCY_CHAIN


class DependencyAnalyzer:
    def map(self, *, failed_service: str | None = None) -> dict[str, Any]:
        chain = list(DEPENDENCY_CHAIN)
        impact = []
        if failed_service:
            if failed_service in chain:
                idx = chain.index(failed_service)
                impact = chain[: idx + 1][::-1]  # upstream dependents conceptually
                # also show downstream
                downstream = chain[idx:]
                impact = list(dict.fromkeys(downstream + impact))
            else:
                impact = [failed_service]
        return {
            "chain": chain,
            "failed_service": failed_service,
            "impacted_services": impact,
            "blast_radius": len(impact),
        }
