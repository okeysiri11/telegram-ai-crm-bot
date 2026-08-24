# ActivityService — interactions and customer timeline (durable).

from __future__ import annotations

from applications.auto_marketplace.crm.models import Interaction, InteractionType
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ActivityService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def record_event(
        self,
        activity_type: InteractionType | str,
        *,
        subject: str,
        body: str = "",
        customer_id: str = "",
        lead_id: str = "",
        deal_id: str = "",
        task_id: str = "",
        agent_id: str = "",
        idempotency_key: str = "",
    ) -> Interaction:
        if isinstance(activity_type, str):
            try:
                activity_type = InteractionType(activity_type)
            except ValueError:
                activity_type = InteractionType.NOTE
        return await self.record(
            Interaction(
                customer_id=customer_id,
                lead_id=lead_id,
                deal_id=deal_id,
                task_id=task_id,
                interaction_type=activity_type,
                subject=subject,
                body=body,
                agent_id=agent_id,
                idempotency_key=idempotency_key,
            )
        )

    async def record(self, interaction: Interaction) -> Interaction:
        if interaction.idempotency_key:
            existing = await self._records().get_activity_by_idempotency(interaction.idempotency_key)
            if existing is not None:
                return existing
        return await self._records().save_activity(interaction)

    async def log_interaction(self, interaction: Interaction) -> Interaction:
        return await self.record(interaction)

    async def get_interaction(self, interaction_id: str) -> Interaction:
        item = await self._records().get_activity(interaction_id)
        if item is None:
            raise NotFoundError("Interaction", interaction_id)
        return item

    async def list_activities(
        self,
        *,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        task_id: str | None = None,
        activity_type: InteractionType | None = None,
    ) -> list[Interaction]:
        items = await self._records().list_activities()
        if customer_id:
            items = [i for i in items if i.customer_id == customer_id]
        if lead_id:
            items = [i for i in items if i.lead_id == lead_id]
        if deal_id:
            items = [i for i in items if i.deal_id == deal_id]
        if task_id:
            items = [i for i in items if i.task_id == task_id]
        if activity_type:
            items = [i for i in items if i.interaction_type == activity_type]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    async def entity_timeline(
        self,
        *,
        customer_id: str = "",
        lead_id: str = "",
        deal_id: str = "",
    ) -> list[dict]:
        items = await self.list_activities(customer_id=customer_id or None, lead_id=lead_id or None, deal_id=deal_id or None)
        if customer_id:
            items = [i for i in items if i.customer_id == customer_id]
        if lead_id:
            items = [i for i in items if i.lead_id == lead_id]
        if deal_id:
            items = [i for i in items if i.deal_id == deal_id]
        return [i.to_dict() for i in items]

    async def customer_timeline(self, customer_id: str) -> dict:
        items = await self.list_activities(customer_id=customer_id)
        records = self._records()
        calls = [c.to_dict() for c in await records.list_calls() if c.customer_id == customer_id]
        emails = [e.to_dict() for e in await records.list_emails() if e.customer_id == customer_id]
        meetings = [m.to_dict() for m in await records.list_meetings() if m.customer_id == customer_id]
        serialized = [i.to_dict() for i in items]
        return {
            "items": serialized,
            "interactions": serialized,
            "calls": calls,
            "emails": emails,
            "meetings": meetings,
        }


activity_service = ActivityService()
