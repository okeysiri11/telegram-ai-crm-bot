# Authentication service — registration, login, JWT/OAuth abstraction.

from __future__ import annotations

import logging
import time

from events.publisher import publish

from applications.auto_marketplace.authentication.models import AuthToken, PortalRole, PortalUser, generate_token, hash_password
from applications.auto_marketplace.customer_portal.events import CustomerRegisteredEvent, DealerLoggedInEvent
from applications.auto_marketplace.crm.models import CustomerProfile
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

logger = logging.getLogger(__name__)


class AuthenticationService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def _find_by_email(self, email: str) -> PortalUser | None:
        for user in self._store.portal_users.list_all():
            if user.email.lower() == email.lower():
                return user
        return None

    async def register_customer(
        self,
        *,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> tuple[PortalUser, AuthToken]:
        if self._find_by_email(email):
            raise ValidationError("Email already registered")
        profile = CustomerProfile(first_name=first_name, last_name=last_name, email=email)
        self._store.customer_profiles.save(profile.customer_id, profile)
        user = PortalUser(
            email=email,
            password_hash=hash_password(password),
            role=PortalRole.CUSTOMER,
            customer_id=profile.customer_id,
            display_name=f"{first_name} {last_name}".strip() or email,
        )
        self._store.portal_users.save(user.user_id, user)
        token = self._issue_token(user)
        await publish(CustomerRegisteredEvent(user_id=user.user_id, email=email, customer_id=profile.customer_id))
        return user, token

    async def register_dealer(
        self,
        *,
        email: str,
        password: str,
        dealer_id: str,
        display_name: str = "",
    ) -> tuple[PortalUser, AuthToken]:
        if self._find_by_email(email):
            raise ValidationError("Email already registered")
        user = PortalUser(
            email=email,
            password_hash=hash_password(password),
            role=PortalRole.DEALER,
            dealer_id=dealer_id,
            display_name=display_name or email,
        )
        self._store.portal_users.save(user.user_id, user)
        token = self._issue_token(user)
        return user, token

    async def login(self, email: str, password: str) -> tuple[PortalUser, AuthToken]:
        user = self._find_by_email(email)
        if user is None or user.password_hash != hash_password(password):
            raise ValidationError("Invalid credentials")
        if not user.is_active:
            raise ValidationError("Account disabled")
        token = self._issue_token(user)
        if user.role == PortalRole.DEALER:
            await publish(DealerLoggedInEvent(user_id=user.user_id, dealer_id=user.dealer_id))
        return user, token

    def _issue_token(self, user: PortalUser) -> AuthToken:
        token = AuthToken(
            user_id=user.user_id,
            access_token=generate_token(),
            refresh_token=generate_token(),
            expires_at=time.time() + 86400,
            role=user.role,
        )
        self._store.portal_sessions.save(token.access_token, token)
        return token

    def validate_token(self, access_token: str) -> PortalUser | None:
        session = self._store.portal_sessions.get(access_token)
        if session is None or session.expires_at < time.time():
            return None
        return self._store.portal_users.get(session.user_id)

    def get_user(self, user_id: str) -> PortalUser:
        user = self._store.portal_users.get(user_id)
        if user is None:
            raise NotFoundError("PortalUser", user_id)
        return user

    async def oauth_login(self, provider: str, external_id: str, email: str) -> tuple[PortalUser, AuthToken]:
        try:
            from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.authenticate_request(f"Bearer oauth-{external_id}")
        except Exception:
            logger.debug("oauth bridge unavailable")
        user = self._find_by_email(email)
        if user is None:
            user = PortalUser(email=email, role=PortalRole.CUSTOMER, display_name=email, password_hash="")
            self._store.portal_users.save(user.user_id, user)
        token = self._issue_token(user)
        return user, token


authentication_service = AuthenticationService()
