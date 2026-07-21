# Communication engine — unified facade for messaging, events, registry, sync.

from __future__ import annotations

from typing import Any

from ecosystem.communication.application_bridge.bridge import ApplicationBridge, application_bridge
from ecosystem.communication.event_bus.bus import EventBus, event_bus
from ecosystem.communication.event_store.store import EventStore, event_store
from ecosystem.communication.message_router.router import MessageRouter, message_router
from ecosystem.communication.service_registry.registry import ServiceRegistry, service_registry
from ecosystem.communication.subscriptions.service import SubscriptionService, subscription_service
from ecosystem.communication.sync.service import SyncService, sync_service
from ecosystem.config import DEFAULT_CONFIG


class CommunicationEngine:
    """Cross-application communication entry point."""

    def __init__(
        self,
        bus: EventBus | None = None,
        router: MessageRouter | None = None,
        registry: ServiceRegistry | None = None,
        store: EventStore | None = None,
        subscriptions: SubscriptionService | None = None,
        sync: SyncService | None = None,
        bridge: ApplicationBridge | None = None,
    ) -> None:
        self.bus = bus or event_bus
        self.router = router or message_router
        self.registry = registry or service_registry
        self.store = store or event_store
        self.subscriptions = subscriptions or subscription_service
        self.sync = sync or sync_service
        self.bridge = bridge or application_bridge

    def metrics(self) -> dict[str, Any]:
        from ecosystem.shared.store import ecosystem_store

        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "communication_layer": DEFAULT_CONFIG.communication_layer,
            "event_bus": DEFAULT_CONFIG.event_bus,
            "bus_events": ecosystem_store.bus_events.count(),
            "messages": ecosystem_store.envelopes.count(),
            "subscriptions": ecosystem_store.subscriptions.count(),
            "registrations": ecosystem_store.registrations.count(),
            "sync_records": ecosystem_store.sync_records.count(),
            "dead_letters": ecosystem_store.dead_letters.count(),
            "shared_contexts": ecosystem_store.shared_contexts.count(),
        }


communication_engine = CommunicationEngine()
