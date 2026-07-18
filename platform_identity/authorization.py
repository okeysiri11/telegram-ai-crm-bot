# Authorization — single entry point for permission checks.

from __future__ import annotations

from platform_identity.exceptions import AuthorizationError
from platform_identity.models import Principal, ResourceRef
from platform_identity.policy_engine import policy_engine


class AuthorizationService:
    @staticmethod
    async def authorize(
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> bool:
        return await policy_engine.authorize(principal, permission, resource=resource)

    @staticmethod
    async def assert_authorized(
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> None:
        await policy_engine.assert_authorized(principal, permission, resource=resource)

    @staticmethod
    async def authorize_realtime_channel(principal: Principal, channel: str) -> bool:
        return await policy_engine.authorize_realtime_channel(principal, channel)

    @staticmethod
    async def assert_realtime_channel(principal: Principal, channel: str) -> None:
        await policy_engine.assert_realtime_channel(principal, channel)

    @staticmethod
    async def has_permission(telegram_id: int, permission: str) -> bool:
        """Backward-compatible helper for legacy call sites."""
        from platform_identity.identity_service import identity_service

        principal = await identity_service.authenticate_telegram(telegram_id)
        return await AuthorizationService.authorize(principal, permission)


authorization_service = AuthorizationService()
