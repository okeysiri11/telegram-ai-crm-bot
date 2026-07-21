# Portal users registry.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.portal.events import PortalUserRegisteredEvent
from applications.agro_marketplace.portal.models import PortalUser
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class UsersService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    async def register(self, user: PortalUser) -> PortalUser:
        if not user.email:
            raise ValidationError("email is required")
        if not user.display_name:
            user.display_name = user.email.split("@")[0]
        saved = self._store.portal_users.save(user.user_id, user)
        await publish(
            PortalUserRegisteredEvent(
                user_id=saved.user_id,
                email=saved.email,
                role=saved.role,
            )
        )
        return saved

    def get(self, user_id: str) -> PortalUser:
        user = self._store.portal_users.get(user_id)
        if user is None:
            raise NotFoundError("PortalUser", user_id)
        return user

    def get_by_email(self, email: str) -> PortalUser | None:
        for user in self._store.portal_users.list_all():
            if user.email.lower() == email.lower():
                return user
        return None

    def list_users(self, *, role: str | None = None) -> list[PortalUser]:
        items = self._store.portal_users.list_all()
        if role:
            items = [u for u in items if u.role == role]
        return items

    def update_profile(self, user_id: str, **fields: object) -> PortalUser:
        user = self.get(user_id)
        for key, value in fields.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        return self._store.portal_users.save(user_id, user)


users_service = UsersService()
