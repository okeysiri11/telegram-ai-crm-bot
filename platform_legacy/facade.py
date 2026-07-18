# LegacyFacade — typed entry point for platform modules.

from __future__ import annotations

from typing import Any

from platform_legacy.registry import legacy_registry


class LegacyFacade:
    """Platform-facing facade; never imports legacy modules directly."""

    @property
    def crm(self) -> Any:
        return legacy_registry.get("crm")

    @property
    def telegram(self) -> Any:
        return legacy_registry.get("telegram")

    @property
    def permissions(self) -> Any:
        return legacy_registry.get("permissions")

    @property
    def notifications(self) -> Any:
        return legacy_registry.get("notification")

    @property
    def audit(self) -> Any:
        return legacy_registry.get("audit")

    @property
    def scheduler(self) -> Any:
        return legacy_registry.get("scheduler")

    @property
    def ai(self) -> Any:
        return legacy_registry.get("ai")

    @property
    def analytics(self) -> Any:
        return legacy_registry.get("analytics")

    @property
    def workflow_rules(self) -> Any:
        return legacy_registry.get("workflow_rules")

    @property
    def sla(self) -> Any:
        return legacy_registry.get("sla")

    @property
    def bootstrap(self) -> Any:
        return legacy_registry.get("bootstrap")

    @property
    def events(self) -> Any:
        return legacy_registry.get("events")

    def metrics(self) -> dict[str, Any]:
        return legacy_registry.snapshot()


legacy = LegacyFacade()
