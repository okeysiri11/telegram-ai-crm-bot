"""Enterprise Event Bus — primary publish/subscribe facade."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.event_platform.event_dispatcher import EventDispatcher
from applications.enterprise_hub.event_platform.event_registry import EventRegistry
from applications.enterprise_hub.event_platform.subscription_manager import SubscriptionManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class EventBus:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = EventRegistry(self.store)
        self.subscriptions = SubscriptionManager(self.store)
        self.dispatcher = EventDispatcher(self.store)

    def publish(self, **kwargs: Any) -> dict[str, Any]:
        return self.dispatcher.publish(**kwargs)

    def subscribe(self, **kwargs: Any) -> dict[str, Any]:
        return self.subscriptions.subscribe(**kwargs)

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "subscriptions": self.subscriptions.status(),
            "dispatches": self.store.evp_dispatches.count(),
        }
