# Migration coverage — platform vs legacy execution path statistics.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MigrationCoverage:
    platform_hits: dict[str, int] = field(default_factory=dict)
    legacy_hits: dict[str, int] = field(default_factory=dict)
    methods: dict[str, dict[str, int]] = field(default_factory=dict)

    def record_platform(self, subsystem: str, *, method: str = "") -> None:
        self.platform_hits[subsystem] = self.platform_hits.get(subsystem, 0) + 1
        if method:
            bucket = self.methods.setdefault(subsystem, {})
            bucket[f"platform:{method}"] = bucket.get(f"platform:{method}", 0) + 1

    def record_legacy(self, subsystem: str, *, method: str = "") -> None:
        self.legacy_hits[subsystem] = self.legacy_hits.get(subsystem, 0) + 1
        if method:
            bucket = self.methods.setdefault(subsystem, {})
            bucket[f"legacy:{method}"] = bucket.get(f"legacy:{method}", 0) + 1

    def subsystem_coverage(self, subsystem: str) -> dict[str, Any]:
        platform = self.platform_hits.get(subsystem, 0)
        legacy = self.legacy_hits.get(subsystem, 0)
        total = platform + legacy
        return {
            "subsystem": subsystem,
            "platform_hits": platform,
            "legacy_hits": legacy,
            "total_hits": total,
            "platform_percent": round(platform / total * 100, 1) if total else 0.0,
        }

    def to_dict(self) -> dict[str, Any]:
        subsystems = sorted(set(self.platform_hits) | set(self.legacy_hits))
        return {
            "platform_hits": dict(self.platform_hits),
            "legacy_hits": dict(self.legacy_hits),
            "methods": dict(self.methods),
            "by_subsystem": [self.subsystem_coverage(name) for name in subsystems],
        }

    def reset(self) -> None:
        self.platform_hits.clear()
        self.legacy_hits.clear()
        self.methods.clear()


migration_coverage = MigrationCoverage()
