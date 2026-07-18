# Identity service — central IAM facade for all platform modules.

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_identity.api_keys import api_key_service
from platform_identity.authentication import authentication_service
from platform_identity.authorization import authorization_service
from platform_identity.jwt_service import jwt_service
from platform_identity.models import AuthMethod, PlatformRole, Principal, ResourceRef
from platform_identity.permission_service import permission_service
from platform_identity.policy_engine import policy_engine
from platform_identity.role_service import role_service
from platform_identity.session_manager import session_manager

logger = logging.getLogger(__name__)


class IdentityService:
    """Single IAM entry point — no module should bypass this for auth decisions."""

    # ---- Authentication ----

    async def authenticate_request(self, request: web.Request) -> Principal:
        return await authentication_service.authenticate_request(request)

    async def authenticate_telegram(self, telegram_id: int) -> Principal:
        return await authentication_service.authenticate_telegram(telegram_id)

    async def login(
        self,
        telegram_id: int,
        *,
        ip: str,
        device: str,
    ) -> dict[str, Any]:
        principal, tokens = await authentication_service.login_with_telegram(
            telegram_id,
            ip=ip,
            device=device,
        )
        return {
            "principal": principal.to_dict(),
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "access_expires_at": tokens.access_expires_at.isoformat(),
            "refresh_expires_at": tokens.refresh_expires_at.isoformat(),
            "session_id": tokens.session_id,
        }

    async def authenticate_for_login(self, request: web.Request, body: dict[str, Any]) -> int:
        """Verify login credentials before issuing JWT — no arbitrary telegram_id."""
        from platform_identity.exceptions import AuthenticationError
        from platform_identity.telegram_login import verify_login_proof, verify_telegram_init_data

        init_data = body.get("telegram_init_data")
        if init_data:
            return verify_telegram_init_data(str(init_data))

        login_proof = body.get("login_proof")
        if login_proof and verify_login_proof(str(login_proof)):
            telegram_id = body.get("telegram_id")
            if telegram_id is None:
                raise AuthenticationError("telegram_id required with login_proof")
            return int(telegram_id)

        try:
            principal = await self.authenticate_request(request)
            if "identity.login" not in (principal.permissions or []) and PlatformRole.OWNER.value not in (
                principal.roles or []
            ):
                raise AuthenticationError("API key lacks identity.login scope")
            telegram_id = body.get("telegram_id")
            if telegram_id is None:
                raise AuthenticationError("telegram_id required for API-key-assisted login")
            return int(telegram_id)
        except AuthenticationError as exc:
            raise AuthenticationError(
                "Login requires telegram_init_data, valid login_proof + telegram_id, "
                "or API key with identity.login scope"
            ) from exc

    async def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        tokens = jwt_service.rotate_refresh_token(refresh_token)
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "access_expires_at": tokens.access_expires_at.isoformat(),
            "refresh_expires_at": tokens.refresh_expires_at.isoformat(),
            "session_id": tokens.session_id,
        }

    async def logout(self, session_id: str) -> None:
        session = session_manager.revoke(session_id)

    async def revoke_token(self, token: str) -> None:
        jwt_service.revoke_token(token)

    # ---- Authorization ----

    async def authorize(
        self,
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> bool:
        return await authorization_service.authorize(principal, permission, resource=resource)

    async def assert_authorized(
        self,
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> None:
        await authorization_service.assert_authorized(principal, permission, resource=resource)

    async def has_permission(self, telegram_id: int, permission: str) -> bool:
        return await authorization_service.has_permission(telegram_id, permission)

    async def has_legacy_permission(self, telegram_id: int, legacy_code: str) -> bool:
        from config import OWNER_ID

        if OWNER_ID is not None and telegram_id == OWNER_ID:
            return True

        principal = await self.authenticate_telegram(telegram_id)
        if principal.is_owner:
            return True

        from platform_identity.permission_service import LEGACY_PERMISSION_MAP

        for iam_code, mapped_legacy in LEGACY_PERMISSION_MAP.items():
            if mapped_legacy == legacy_code:
                if await self.authorize(principal, iam_code):
                    return True

        try:
            from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

            return await PlatformPermissionsEngineV1.user_has_permission(telegram_id, legacy_code)
        except Exception:
            return False

    async def authorize_realtime_channel(self, principal: Principal, channel: str) -> bool:
        return await authorization_service.authorize_realtime_channel(principal, channel)

    async def assert_realtime_channel(self, principal: Principal, channel: str) -> None:
        await authorization_service.assert_realtime_channel(principal, channel)

    # ---- Management role bridge (backward compat) ----

    async def resolve_management_role(
        self,
        telegram_id: int | None = None,
        *,
        principal: Principal | None = None,
    ):
        from platform_management.exceptions import ManagementPermissionError
        from platform_management.permissions import ManagementRole

        if principal is not None:
            if PlatformRole.OWNER.value in principal.roles:
                return ManagementRole.OWNER
            if PlatformRole.ADMINISTRATOR.value in principal.roles:
                return ManagementRole.ADMINISTRATOR
            if principal.auth_method == AuthMethod.API_KEY:
                scopes = set(principal.permissions or [])
                if "management.admin" in scopes or "management.write" in scopes:
                    return ManagementRole.ADMINISTRATOR
                if scopes or principal.roles:
                    return ManagementRole.READ_ONLY
            if PlatformRole.READ_ONLY.value in principal.roles or principal.roles:
                return ManagementRole.READ_ONLY
            if principal.permissions:
                return ManagementRole.READ_ONLY
            raise ManagementPermissionError(
                f"Principal {principal.principal_id} lacks management API access"
            )

        if telegram_id is None:
            raise ManagementPermissionError("actor_telegram_id is required")

        principal = await self.authenticate_telegram(telegram_id)

        if PlatformRole.OWNER.value in principal.roles:
            return ManagementRole.OWNER
        if PlatformRole.ADMINISTRATOR.value in principal.roles:
            return ManagementRole.ADMINISTRATOR
        if PlatformRole.READ_ONLY.value in principal.roles or principal.roles:
            return ManagementRole.READ_ONLY

        raise ManagementPermissionError(f"Actor {telegram_id} lacks management API access")

    # ---- IAM administration ----

    def list_users(self) -> list[dict[str, Any]]:
        sessions = session_manager.active_sessions()
        users: dict[int, dict[str, Any]] = {}
        for session in sessions:
            if session.telegram_id is None:
                continue
            entry = users.setdefault(
                session.telegram_id,
                {
                    "telegram_id": session.telegram_id,
                    "sessions": [],
                    "roles": session.roles,
                },
            )
            entry["sessions"].append(session.to_dict())
        return list(users.values())

    def list_roles(self) -> dict[str, Any]:
        from platform_identity.role_service import ROLE_INHERITANCE

        return {
            "roles": role_service.list_roles(),
            "inheritance": {role: list(parents) for role, parents in ROLE_INHERITANCE.items()},
        }

    def list_permissions(self) -> dict[str, Any]:
        return {
            "permissions": permission_service.list_permissions(),
            "tree": permission_service.permission_tree(),
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in session_manager.list_sessions()]

    def list_api_keys(self) -> list[dict[str, Any]]:
        return [k.to_dict() for k in api_key_service.list_keys()]

    def list_policies(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in policy_engine.list_policies()]

    def status(self) -> dict[str, Any]:
        return {
            "users": self.list_users(),
            "roles": self.list_roles(),
            "permissions": self.list_permissions(),
            "sessions": self.list_sessions(),
            "api_keys": self.list_api_keys(),
            "policies": self.list_policies(),
            "realtime_permission_matrix": policy_engine.permission_matrix(),
        }

    def reset(self) -> None:
        session_manager.reset()
        api_key_service.reset()
        jwt_service.reset()
        policy_engine.reset()


identity_service = IdentityService()
