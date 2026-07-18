# VerticalBuilder — construct fully wired vertical instances.

from __future__ import annotations

import logging
from typing import Type

from platform_sdk.base_vertical import PlatformVertical
from platform_sdk.event_provider import EventProvider, event_provider
from platform_sdk.manager_provider import ManagerProvider, manager_provider
from platform_sdk.notification_provider import NotificationProvider, notification_provider
from platform_sdk.platform_context import PlatformContext
from platform_sdk.validation_provider import ValidationProvider, validation_provider
from platform_sdk.vertical_registry import VerticalRegistry, vertical_registry
from platform_sdk.workflow_loader import SdkWorkflowLoader, sdk_workflow_loader

logger = logging.getLogger(__name__)


class VerticalBuilder:
    """Build verticals with injected repositories/services/providers."""

    def __init__(
        self,
        *,
        registry: VerticalRegistry | None = None,
        manager: ManagerProvider | None = None,
        notifications: NotificationProvider | None = None,
        validation: ValidationProvider | None = None,
        events: EventProvider | None = None,
        workflows: SdkWorkflowLoader | None = None,
    ) -> None:
        self.registry = registry or vertical_registry
        self._manager = manager or manager_provider
        self._notifications = notifications or notification_provider
        self._validation = validation or validation_provider
        self._events = events or event_provider
        self._workflows = workflows or sdk_workflow_loader

    def create_context(self, **metadata) -> PlatformContext:
        self._workflows.ensure_loaded()
        return PlatformContext(
            manager=self._manager,
            notifications=self._notifications,
            validation=self._validation,
            events=self._events,
            workflows=self._workflows,
            metadata=dict(metadata),
        )

    def build(self, vertical_cls: Type[PlatformVertical]) -> PlatformVertical:
        ctx = self.create_context(vertical_code=vertical_cls.vertical_code)
        instance = vertical_cls.build(ctx)
        self.registry.set_built(vertical_cls.vertical_code, instance)
        return instance

    def build_all(self) -> dict[str, PlatformVertical]:
        built: dict[str, PlatformVertical] = {}
        for code in self.registry.list_codes():
            cls = self.registry.get(code)
            built[code] = self.build(cls)
        logger.info("verticals_built count=%s", len(built))
        return built

    def build_by_code(self, code: str) -> PlatformVertical:
        return self.build(self.registry.get(code))


vertical_builder = VerticalBuilder()
