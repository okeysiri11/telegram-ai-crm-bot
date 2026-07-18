# PlatformContext — dependency container for vertical operations.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from platform_sdk.event_provider import EventProvider
    from platform_sdk.manager_provider import ManagerProvider
    from platform_sdk.notification_provider import NotificationProvider
    from platform_sdk.validation_provider import ValidationProvider
    from platform_sdk.workflow_loader import SdkWorkflowLoader


@dataclass
class PlatformContext:
    """Injected into every built vertical — no direct SQL from handlers."""

    manager: ManagerProvider
    notifications: NotificationProvider
    validation: ValidationProvider
    events: EventProvider
    workflows: SdkWorkflowLoader
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **extra: Any) -> PlatformContext:
        merged = {**self.metadata, **extra}
        return PlatformContext(
            manager=self.manager,
            notifications=self.notifications,
            validation=self.validation,
            events=self.events,
            workflows=self.workflows,
            metadata=merged,
        )
