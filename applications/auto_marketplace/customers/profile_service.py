# CustomerProfileService — enterprise customer CRUD and segmentation.

from __future__ import annotations

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import CustomerCreatedEvent
from applications.auto_marketplace.crm.models import CustomerProfile
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Customer
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CustomerProfileService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant

    async def create(self, profile: CustomerProfile) -> CustomerProfile:
        profile.segment = await self._ai.segment_customer(profile)
        saved = self._store.customer_profiles.save(profile.customer_id, profile)
        # Sync legacy customer store
        self._store.customers.save(
            profile.customer_id,
            Customer(
                customer_id=profile.customer_id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile.email,
                phone=profile.phone,
                preferences=profile.preferences,
            ),
        )
        await publish(CustomerCreatedEvent(customer_id=saved.customer_id, email=saved.email))
        return saved

    def get(self, customer_id: str) -> CustomerProfile:
        profile = self._store.customer_profiles.get(customer_id)
        if profile is None:
            raise NotFoundError("CustomerProfile", customer_id)
        return profile

    def list_profiles(self, *, segment: str | None = None) -> list[CustomerProfile]:
        items = self._store.customer_profiles.list_all()
        if segment:
            items = [p for p in items if p.segment == segment]
        return items

    async def update(self, customer_id: str, **updates: object) -> CustomerProfile:
        profile = self.get(customer_id)
        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        profile.segment = await self._ai.segment_customer(profile)
        return self._store.customer_profiles.save(customer_id, profile)


customer_profile_service = CustomerProfileService()
