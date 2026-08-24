# CustomerProfileService — enterprise customer CRUD and segmentation.

from __future__ import annotations

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import CustomerCreatedEvent
from applications.auto_marketplace.crm.models import CustomerProfile
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CustomerProfileService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def create(self, profile: CustomerProfile) -> CustomerProfile:
        profile.segment = await self._ai.segment_customer(profile)
        saved = await self._records().save_customer(profile)
        await publish(CustomerCreatedEvent(customer_id=saved.customer_id, email=saved.email))
        from applications.auto_marketplace.activities.service import activity_service

        await activity_service.record_event(
            "customer_created",
            subject="Customer created",
            body=saved.email,
            customer_id=saved.customer_id,
            agent_id=saved.owner_agent_id,
            idempotency_key=f"customer_created:{saved.customer_id}",
        )
        return saved

    async def get(self, customer_id: str) -> CustomerProfile:
        profile = await self._records().get_customer(customer_id)
        if profile is None:
            raise NotFoundError("CustomerProfile", customer_id)
        return profile

    async def list_profiles(self, *, segment: str | None = None, email: str | None = None) -> list[CustomerProfile]:
        items = await self._records().list_customers()
        if segment:
            items = [p for p in items if p.segment == segment]
        if email:
            needle = email.lower().strip()
            items = [p for p in items if (p.email or "").lower() == needle]
        return items

    async def update(self, customer_id: str, **updates: object) -> CustomerProfile:
        profile = await self.get(customer_id)
        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        profile.segment = await self._ai.segment_customer(profile)
        saved = await self._records().save_customer(profile)
        return saved

    async def delete(self, customer_id: str) -> bool:
        await self.get(customer_id)
        return await self._records().delete_customer(customer_id)


customer_profile_service = CustomerProfileService()
