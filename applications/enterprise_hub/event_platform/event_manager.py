"""Event manager — high-level catalog and ops helpers."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.event_platform.event_bus import EventBus
from applications.enterprise_hub.event_platform.event_registry import EventRegistry
from applications.enterprise_hub.event_platform.event_store import EventStore
from applications.enterprise_hub.event_platform.models import EVENT_TYPES
from applications.enterprise_hub.event_platform.schema_registry import SchemaRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class EventManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = EventRegistry(self.store)
        self.schemas = SchemaRegistry(self.store)
        self.store_engine = EventStore(self.store)
        self.bus = EventBus(self.store)

    def bootstrap_catalog(self) -> list[dict[str, Any]]:
        registered = []
        for et in EVENT_TYPES:
            typ = self.registry.register_type(event_type=et, version="1.0", severity="normal" if et != "SecurityAlert" else "critical")
            sch = self.schemas.register(
                event_type=et,
                version="1.0",
                fields=["id", "timestamp", "entity_id"],
            )
            registered.append({"type_id": typ["type_id"], "schema_id": sch["schema_id"], "event_type": et})
        return registered

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "schemas": self.schemas.status(),
            "store": self.store_engine.status(),
            "bus": self.bus.status(),
        }
