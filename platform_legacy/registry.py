# LegacyRegistry — register and resolve legacy adapters.

from __future__ import annotations

from typing import Any

from platform_legacy.adapter import (
    AIAdapter,
    AnalyticsAdapter,
    AuditAdapter,
    BootstrapAdapter,
    CRMAdapter,
    LegacyEventsAdapter,
    NotificationAdapter,
    PermissionsAdapter,
    SchedulerAdapter,
    SlaAdapter,
    TelegramAdapter,
    WorkflowRulesAdapter,
)
from platform_legacy.models import LegacyMetrics, MigrationProgress


class LegacyRegistry:
    """Central registry for legacy subsystem adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}
        self._metrics = LegacyMetrics()
        self._pending_replacements = [
            "handlers.py",
            "database_legacy.py",
            "services/pg_*",
            "openrouter.py",
        ]

    @property
    def metrics(self) -> LegacyMetrics:
        return self._metrics

    def record_call(self, record: Any) -> None:
        self._metrics.total_calls += 1
        self._metrics.calls_by_adapter[record.adapter] = (
            self._metrics.calls_by_adapter.get(record.adapter, 0) + 1
        )
        if not record.success:
            self._metrics.total_errors += 1
            self._metrics.errors_by_adapter[record.adapter] = (
                self._metrics.errors_by_adapter.get(record.adapter, 0) + 1
            )
        self._metrics.recent_calls.append(record)
        if len(self._metrics.recent_calls) > 200:
            self._metrics.recent_calls = self._metrics.recent_calls[-200:]

    def record_deprecated(self, api_name: str) -> None:
        self._metrics.deprecated_api_hits[api_name] = (
            self._metrics.deprecated_api_hits.get(api_name, 0) + 1
        )

    def register(self, name: str, adapter: Any) -> None:
        self._adapters[name] = adapter

    def get(self, name: str) -> Any:
        if name not in self._adapters:
            raise KeyError(f"Legacy adapter not registered: {name}")
        return self._adapters[name]

    def list_adapters(self) -> list[str]:
        return sorted(self._adapters)

    def migration_progress(self) -> MigrationProgress:
        registered = self.list_adapters()
        wired = [name for name in registered if self._adapters.get(name) is not None]
        return MigrationProgress(
            registered_adapters=registered,
            wired_adapters=wired,
            pending_replacements=list(self._pending_replacements),
            isolation_enforced=True,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "metrics": self._metrics.to_dict(),
            "migration": self.migration_progress().to_dict(),
            "adapters": self.list_adapters(),
        }

    def wire_defaults(self) -> None:
        """Register all standard adapters with shared metrics."""
        self.register("crm", CRMAdapter(registry=self))
        self.register("telegram", TelegramAdapter(registry=self))
        self.register("permissions", PermissionsAdapter(registry=self))
        self.register("notification", NotificationAdapter(registry=self))
        self.register("audit", AuditAdapter(registry=self))
        self.register("scheduler", SchedulerAdapter(registry=self))
        self.register("ai", AIAdapter(registry=self))
        self.register("analytics", AnalyticsAdapter(registry=self))
        self.register("workflow_rules", WorkflowRulesAdapter(registry=self))
        self.register("sla", SlaAdapter(registry=self))
        self.register("bootstrap", BootstrapAdapter(registry=self))
        self.register("events", LegacyEventsAdapter(registry=self))


legacy_registry = LegacyRegistry()
legacy_registry.wire_defaults()
