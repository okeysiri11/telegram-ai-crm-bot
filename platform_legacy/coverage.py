# Migration coverage — platform vs legacy execution path statistics.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MigrationCoverage:
    platform_hits: dict[str, int] = field(default_factory=dict)
    legacy_hits: dict[str, int] = field(default_factory=dict)
    fallback_hits: dict[str, int] = field(default_factory=dict)
    error_hits: dict[str, int] = field(default_factory=dict)
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

    def record_fallback(self, subsystem: str, *, reason: str = "") -> None:
        self.fallback_hits[subsystem] = self.fallback_hits.get(subsystem, 0) + 1
        if reason:
            bucket = self.methods.setdefault(subsystem, {})
            bucket[f"fallback:{reason}"] = bucket.get(f"fallback:{reason}", 0) + 1

    def record_error(self, subsystem: str, *, method: str = "") -> None:
        self.error_hits[subsystem] = self.error_hits.get(subsystem, 0) + 1
        if method:
            bucket = self.methods.setdefault(subsystem, {})
            bucket[f"error:{method}"] = bucket.get(f"error:{method}", 0) + 1

    @property
    def total_platform(self) -> int:
        return sum(self.platform_hits.values())

    @property
    def total_legacy(self) -> int:
        return sum(self.legacy_hits.values())

    @property
    def migration_percent(self) -> float:
        total = self.total_platform + self.total_legacy
        if total == 0:
            return 0.0
        return round(self.total_platform / total * 100, 1)

    def migrated_components(self) -> list[str]:
        return sorted(
            name
            for name in set(self.platform_hits) | set(self.legacy_hits)
            if self.platform_hits.get(name, 0) > 0
        )

    def remaining_legacy_components(self) -> list[str]:
        return sorted(
            name for name, hits in self.legacy_hits.items() if hits > 0 and self.platform_hits.get(name, 0) == 0
        )

    def subsystem_coverage(self, subsystem: str) -> dict[str, Any]:
        platform = self.platform_hits.get(subsystem, 0)
        legacy = self.legacy_hits.get(subsystem, 0)
        total = platform + legacy
        return {
            "subsystem": subsystem,
            "platform_hits": platform,
            "legacy_hits": legacy,
            "fallback_hits": self.fallback_hits.get(subsystem, 0),
            "error_hits": self.error_hits.get(subsystem, 0),
            "total_hits": total,
            "platform_percent": round(platform / total * 100, 1) if total else 0.0,
        }

    def coverage_report(self) -> dict[str, Any]:
        subsystems = sorted(set(self.platform_hits) | set(self.legacy_hits) | set(self.fallback_hits))
        return {
            "migration_percent": self.migration_percent,
            "migrated_components": self.migrated_components(),
            "remaining_legacy": self.remaining_legacy_components(),
            "platform_total": self.total_platform,
            "legacy_total": self.total_legacy,
            "fallback_total": sum(self.fallback_hits.values()),
            "error_total": sum(self.error_hits.values()),
            "by_subsystem": [self.subsystem_coverage(name) for name in subsystems],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_hits": dict(self.platform_hits),
            "legacy_hits": dict(self.legacy_hits),
            "fallback_hits": dict(self.fallback_hits),
            "error_hits": dict(self.error_hits),
            "methods": dict(self.methods),
            "report": self.coverage_report(),
        }

    def reset(self) -> None:
        self.platform_hits.clear()
        self.legacy_hits.clear()
        self.fallback_hits.clear()
        self.error_hits.clear()
        self.methods.clear()


migration_coverage = MigrationCoverage()
