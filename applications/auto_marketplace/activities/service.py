# ActivityService — interactions and customer timeline.

from __future__ import annotations

from applications.auto_marketplace.crm.models import Interaction
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ActivityService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def log_interaction(self, interaction: Interaction) -> Interaction:
        return self._store.interactions.save(interaction.interaction_id, interaction)

    def get_interaction(self, interaction_id: str) -> Interaction:
        item = self._store.interactions.get(interaction_id)
        if item is None:
            raise NotFoundError("Interaction", interaction_id)
        return item

    def customer_timeline(self, customer_id: str) -> list[dict]:
        items = [i for i in self._store.interactions.list_all() if i.customer_id == customer_id]
        calls = [c.to_dict() for c in self._store.phone_calls.list_all() if c.customer_id == customer_id]
        emails = [e.to_dict() for e in self._store.email_messages.list_all() if e.customer_id == customer_id]
        meetings = [m.to_dict() for m in self._store.meetings.list_all() if m.customer_id == customer_id]
        timeline = [i.to_dict() for i in sorted(items, key=lambda x: x.created_at, reverse=True)]
        return {"interactions": timeline, "calls": calls, "emails": emails, "meetings": meetings}


activity_service = ActivityService()
