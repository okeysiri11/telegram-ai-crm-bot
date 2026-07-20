# AuthenticationProvider — API keys, JWT, OAuth, service accounts, anonymous.

from __future__ import annotations

import logging
from typing import Any

from platform_security.config import DEFAULT_SECURITY_CONFIG, SecurityConfig
from platform_security.exceptions import AuthenticationFailedError
from platform_security.models import AuthMethodType, SecurityPrincipal
from platform_security.roles import role_manager

logger = logging.getLogger(__name__)


class OAuthProvider:
    """OAuth abstraction — register provider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider

    async def authenticate(self, provider_name: str, token: str, **kwargs: Any) -> SecurityPrincipal:
        if provider_name not in self._providers:
            raise AuthenticationFailedError(f"OAuth provider not registered: {provider_name}")
        provider = self._providers[provider_name]
        if hasattr(provider, "authenticate"):
            result = await provider.authenticate(token, **kwargs)
            if isinstance(result, SecurityPrincipal):
                return result
        raise AuthenticationFailedError("OAuth authentication failed")


class AuthenticationProvider:
    def __init__(self, *, config: SecurityConfig | None = None) -> None:
        self._config = config or DEFAULT_SECURITY_CONFIG
        self._oauth = OAuthProvider()

    @property
    def oauth(self) -> OAuthProvider:
        return self._oauth

    async def authenticate_api_key(self, raw_key: str) -> SecurityPrincipal:
        try:
            from platform_identity.api_keys import api_key_service

            identity = await api_key_service.authenticate(raw_key)
            roles = [role_manager.map_identity_role(r) for r in identity.roles]
            return SecurityPrincipal(
                principal_id=identity.principal_id,
                auth_method=AuthMethodType.API_KEY,
                roles=roles,
                permissions=list(identity.permissions),
            )
        except Exception as exc:
            logger.debug("api_key auth bridge failed: %s", exc)
            raise AuthenticationFailedError("Invalid API key") from exc

    async def authenticate_jwt(self, token: str) -> SecurityPrincipal:
        try:
            from platform_identity.jwt_service import jwt_service

            claims = jwt_service.verify_access_token(token)
            roles = [role_manager.map_identity_role(r) for r in claims.get("roles", ["viewer"])]
            perms = list(role_manager.effective_permissions(roles))
            return SecurityPrincipal(
                principal_id=str(claims.get("sub", "unknown")),
                auth_method=AuthMethodType.JWT,
                roles=roles,
                permissions=perms,
                session_id=claims.get("session_id"),
            )
        except Exception as exc:
            logger.debug("jwt auth bridge failed: %s", exc)
            raise AuthenticationFailedError("JWT authentication failed") from exc

    async def authenticate_service_account(self, account_id: str, credential: str) -> SecurityPrincipal:
        if not self._config.service_account_enabled:
            raise AuthenticationFailedError("Service accounts disabled")
        if not account_id or not credential:
            raise AuthenticationFailedError("Invalid service account credentials")
        return SecurityPrincipal(
            principal_id=f"service:{account_id}",
            auth_method=AuthMethodType.SERVICE_ACCOUNT,
            roles=[role_manager.map_identity_role("service")],
            permissions=list(role_manager.permissions_for_role("service")),
            service_account_id=account_id,
        )

    async def authenticate_anonymous(self) -> SecurityPrincipal:
        if not self._config.allow_anonymous:
            raise AuthenticationFailedError("Anonymous access disabled")
        return SecurityPrincipal(
            principal_id="anonymous",
            auth_method=AuthMethodType.ANONYMOUS,
            roles=["viewer"],
            permissions=["workflow.read", "tool.read", "agent.read"],
        )

    async def authenticate(
        self,
        *,
        api_key: str | None = None,
        jwt_token: str | None = None,
        oauth_provider: str | None = None,
        oauth_token: str | None = None,
        service_account_id: str | None = None,
        service_credential: str | None = None,
        anonymous: bool = False,
    ) -> SecurityPrincipal:
        if api_key and self._config.api_key_enabled:
            return await self.authenticate_api_key(api_key)
        if jwt_token and self._config.jwt_enabled:
            return await self.authenticate_jwt(jwt_token)
        if oauth_provider and oauth_token and self._config.oauth_enabled:
            return await self._oauth.authenticate(oauth_provider, oauth_token)
        if service_account_id and service_credential:
            return await self.authenticate_service_account(service_account_id, service_credential)
        if anonymous:
            return await self.authenticate_anonymous()
        raise AuthenticationFailedError("No valid authentication credentials provided")


authentication_provider = AuthenticationProvider()
