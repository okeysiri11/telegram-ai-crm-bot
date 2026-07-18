# Event bus adapters — route legacy and CRM buses through PlatformEventBus.

from events.adapters.crm_adapter import publish_crm_to_platform_bus
from events.adapters.legacy_adapter import (
    publish_legacy_to_platform_bus,
    register_legacy_handlers_on_platform_bus,
)

__all__ = [
    "publish_crm_to_platform_bus",
    "publish_legacy_to_platform_bus",
    "register_legacy_handlers_on_platform_bus",
]
