# Authentication — Telegram, JWT, API keys, service accounts, OAuth stub.

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_identity.api_keys import KEY_PREFIX, api_key_service
from platform_identity.audit_hooks import iam_audit
from platform_identity.exceptions import ApiKeyError, AuthenticationError
from platform_identity.jwt_service import jwt_service
from platform_identity.models import AuthMethod, PlatformRole, Principal
from platform_identity.permission_service import permission_service
from platform_identity.role_service import role_service
from platform_identity.session_manager import session_manager

logger = logging.getLogger(__name__)


class OAuthProviderStub:
    """Placeholder for future OAuth providers (Google, GitHub, etc.)."""

    provider_name: str = "oauth"

    async def authenticate(self, _request: web.Request) -> Principal:
        raise AuthenticationError("OAuth providers not yet configured")


class AuthenticationService:
    def __init__(self) -> None:
        self._oauth_providers: dict[str, OAuthProviderStub] = {}

    def register_oauth_provider(self, name: str, provider: OAuthProviderStub) -> None:
        self._oauth_providers[name] = provider

    async def authenticate_request(self, request: web.Request) -> Principal:
        ip = _client_ip(request)
        device = request.headers.get("User-Agent", "unknown")

        try:
            principal = await self._try_authenticate(request)
            await iam_audit.log_authentication(
                principal=principal,
                method=principal.auth_method.value,
                success=True,
                ip=ip,
            )
            if principal.session_id:
                session_manager.touch(principal.session_id)
            return principal
        except AuthenticationError as exc:
            await iam_audit.log_authentication(
                principal=None,
                method="unknown",
                success=False,
                ip=ip,
                details={"error": str(exc)},
            )
            raise

    async def authenticate_telegram(self, telegram_id: int) -> Principal:
        from config import OWNER_ID

        if OWNER_ID is not None and telegram_id == OWNER_ID:
            roles = [PlatformRole.OWNER.value]
            auth_method = AuthMethod.TELEGRAM_OWNER
        else:
            roles = await role_service.roles_for_telegram_user(telegram_id)
            auth_method = AuthMethod.TELEGRAM_USER

        permissions = sorted(
            await permission_service.resolve_user_permissions(telegram_id, roles)
        )
        return Principal(
            principal_id=f"telegram:{telegram_id}",
            auth_method=auth_method,
            roles=roles,
            permissions=permissions,
            telegram_id=telegram_id,
        )

    async def authenticate_service_account(self, account_id: str, *, roles: list[str] | None = None) -> Principal:
        assigned = roles or [PlatformRole.SERVICE.value]
        perms: set[str] = set()
        for role in assigned:
            perms.update(role_service.permissions_for_role(role))
        return Principal(
            principal_id=f"service:{account_id}",
            auth_method=AuthMethod.SERVICE_ACCOUNT,
            roles=assigned,
            permissions=sorted(perms),
            service_account_id=account_id,
        )

    async def login_with_telegram(
        self,
        telegram_id: int,
        *,
        ip: str,
        device: str,
    ) -> tuple[Principal, Any]:
        from platform_identity.jwt_service import jwt_service as jwt_svc
        from platform_identity.models import TokenPair

        principal = await self.authenticate_telegram(telegram_id)
        session = session_manager.create_session(
            principal=principal,
            ip=ip,
            device=device,
        )
        tokens = jwt_svc.issue_tokens(
            subject=principal.principal_id,
            roles=principal.roles,
            permissions=principal.permissions,
            telegram_id=telegram_id,
            session_id=session.session_id,
        )
        session.refresh_token_id = jwt_svc.fingerprint(tokens.refresh_token)
        await iam_audit.log_session_created(
            principal=principal,
            session_id=session.session_id,
            ip=ip,
            device=device,
        )
        return principal, tokens

    async def _try_authenticate(self, request: web.Request) -> Principal:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token.startswith(KEY_PREFIX):
                return await _authenticate_api_key(token)
            return await _authenticate_jwt(token)

        api_key = request.headers.get("X-API-Key", "").strip()
        if api_key:
            return await _authenticate_api_key(api_key)

        oauth_provider = request.query.get("oauth_provider")
        if oauth_provider:
            provider = self._oauth_providers.get(oauth_provider)
            if provider is None:
                raise AuthenticationError(f"Unknown OAuth provider: {oauth_provider}")
            return await provider.authenticate(request)

        raise AuthenticationError(
            "Authentication required: provide Authorization Bearer JWT or X-API-Key header"
        )


async def _authenticate_api_key(raw_key: str) -> Principal:
    try:
        return await api_key_service.authenticate(raw_key)
    except ApiKeyError as exc:
        raise AuthenticationError(str(exc)) from exc


async def _authenticate_jwt(token: str) -> Principal:
    from platform_identity.exceptions import TokenError

    try:
        claims = jwt_service.verify_access_token(token)
    except TokenError as exc:
        raise AuthenticationError(str(exc)) from exc
    roles = list(claims.get("roles", []))
    permissions = list(claims.get("permissions", []))
    session_id = claims.get("session_id")
    if session_id:
        session_manager.validate(session_id)

    telegram_id = claims.get("telegram_id")
    if telegram_id is not None:
        try:
            telegram_id = int(telegram_id)
        except (TypeError, ValueError):
            telegram_id = None

    return Principal(
        principal_id=str(claims.get("sub", "")),
        auth_method=AuthMethod.JWT,
        roles=roles,
        permissions=permissions,
        telegram_id=telegram_id,
        session_id=session_id,
    )


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "unknown"


authentication_service = AuthenticationService()
