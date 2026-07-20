# Portal profile management.

from __future__ import annotations

from applications.auto_marketplace.authentication.models import PortalUser
from applications.auto_marketplace.authentication.service import AuthenticationService, authentication_service
from applications.auto_marketplace.crm.models import CustomerProfile
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ProfileService:
    def __init__(self, store: MarketplaceStore | None = None, auth: AuthenticationService | None = None) -> None:
        self._store = store or marketplace_store
        self._auth = auth or authentication_service

    def get_portal_user(self, user_id: str) -> PortalUser:
        return self._auth.get_user(user_id)

    def update_portal_user(self, user_id: str, *, display_name: str = "", metadata: dict | None = None) -> PortalUser:
        user = self._auth.get_user(user_id)
        if display_name:
            user.display_name = display_name
        if metadata:
            user.metadata.update(metadata)
        return self._store.portal_users.save(user_id, user)

    def get_customer_profile(self, customer_id: str) -> CustomerProfile | None:
        return self._store.customer_profiles.get(customer_id)

    async def update_customer_profile(self, customer_id: str, **fields) -> CustomerProfile:
        profile = self._store.customer_profiles.get(customer_id)
        if profile is None:
            profile = CustomerProfile(customer_id=customer_id)
        for key, value in fields.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        return self._store.customer_profiles.save(customer_id, profile)


profile_service = ProfileService()
