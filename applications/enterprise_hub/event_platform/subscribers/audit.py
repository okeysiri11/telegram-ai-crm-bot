"""AuditSubscriber."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.event_platform.subscription_manager import SubscriptionManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AuditSubscriber:
    name = "audit"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.subscriptions = SubscriptionManager(store or enterprise_hub_store)

    def subscribe(self, *, event_types: list[str], filter_severity: str | None = None) -> dict[str, Any]:
        return self.subscriptions.subscribe(
            subscriber=self.name,
            event_types=event_types,
            filter_severity=filter_severity,
        )
