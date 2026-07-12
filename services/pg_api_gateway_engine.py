# Public API Gateway v1 — authentication, rate limiting, client management.

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from config import OWNER_ID
from database.models.api_gateway import ApiClientStatus, ApiKeyStatus
from database.models.audit_log import AuditAction
from database.session import get_session
from repositories.api_gateway_repository import (
    ApiClientRepository,
    ApiKeyRepository,
    ApiRateLimitRepository,
    ApiUsageLogRepository,
)
from repositories.audit_repository import AuditRepository
from repositories.user_role_repository import UserRoleRepository

GATEWAY_ROLES = frozenset({"OWNER", "ADMIN"})
API_JWT_SECRET = os.getenv("API_JWT_SECRET", "change-me-in-production-api-jwt-secret")
API_JWT_ALGORITHM = "HS256"
API_JWT_TTL_HOURS = int(os.getenv("API_JWT_TTL_HOURS", "24"))
API_KEY_PREFIX = "gw_live_"

DEFAULT_CLIENT_PERMISSIONS: frozenset[str] = frozenset({
    "deal.read",
    "deal.write",
    "partner.read",
    "partner.write",
    "pricing.read",
    "fx.read",
    "vehicle.read",
    "vehicle.write",
    "inventory.read",
    "order.read",
    "order.write",
    "document.read",
    "document.write",
    "notification.read",
    "notification.write",
})

ENDPOINT_PERMISSIONS: dict[tuple[str, str], str] = {
    ("GET", "/v1/deals"): "deal.read",
    ("POST", "/v1/deals"): "deal.write",
    ("GET", "/v1/partners"): "partner.read",
    ("POST", "/v1/partners"): "partner.write",
    ("GET", "/v1/pricing"): "pricing.read",
    ("POST", "/v1/pricing/calculate"): "pricing.read",
    ("GET", "/v1/fx"): "fx.read",
    ("GET", "/v1/fx/rates"): "fx.read",
    ("GET", "/v1/vehicles"): "vehicle.read",
    ("POST", "/v1/vehicles"): "vehicle.write",
    ("GET", "/v1/inventory"): "inventory.read",
    ("GET", "/v1/orders"): "order.read",
    ("POST", "/v1/orders"): "order.write",
    ("GET", "/v1/documents"): "document.read",
    ("POST", "/v1/documents"): "document.write",
    ("GET", "/v1/notifications"): "notification.read",
    ("POST", "/v1/notifications"): "notification.write",
}


@dataclass
class ApiAuthContext:
    client_id: uuid.UUID
    client_code: str
    permissions: set[str] = field(default_factory=set)
    key_id: uuid.UUID | None = None
    actor_user_id: int = OWNER_ID
    auth_method: str = "api_key"


class ApiGatewayEngineError(Exception):
    pass


class ApiAuthenticationError(ApiGatewayEngineError):
    pass


class ApiPermissionError(ApiGatewayEngineError):
    pass


class ApiRateLimitError(ApiGatewayEngineError):
    pass


class ApiGatewayEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in GATEWAY_ROLES for role in roles)

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _client_snapshot(client) -> dict[str, Any]:
        return {
            "id": str(client.id),
            "client_id": client.client_id,
            "name": client.name,
            "description": client.description,
            "status": client.status,
            "permissions": client.permissions or [],
            "owner_user_id": client.owner_user_id,
            "created_at": client.created_at.isoformat(),
        }

    @staticmethod
    def _key_snapshot(key, *, include_secret: bool = False) -> dict[str, Any]:
        data = {
            "id": str(key.id),
            "client_id": str(key.client_id),
            "name": key.name,
            "key_prefix": key.key_prefix,
            "status": key.status,
            "permissions": key.permissions,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        }
        if include_secret:
            data["api_key"] = key  # placeholder overwritten by caller
        return data

    @staticmethod
    def required_permission(method: str, path: str) -> str | None:
        normalized = path.rstrip("/") or "/"
        return ENDPOINT_PERMISSIONS.get((method.upper(), normalized))

    @staticmethod
    def _resolve_permissions(client, key=None) -> set[str]:
        if key and key.permissions:
            return set(key.permissions)
        if client.permissions:
            return set(client.permissions)
        return set(DEFAULT_CLIENT_PERMISSIONS)

    @staticmethod
    async def create_client(
        actor_id: int,
        *,
        client_id: str,
        name: str,
        permissions: list[str] | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await ApiGatewayEngineV1.user_can_access(actor_id):
            raise ApiGatewayEngineError("Access denied")

        perms = permissions or sorted(DEFAULT_CLIENT_PERMISSIONS)
        async with get_session() as session:
            if await ApiClientRepository(session).get_by_client_id(client_id):
                raise ApiGatewayEngineError(f"Client already exists: {client_id}")

            client = await ApiClientRepository(session).create(
                client_id=client_id,
                name=name,
                permissions=perms,
                owner_user_id=fields.pop("owner_user_id", actor_id),
                **fields,
            )

            await ApiRateLimitRepository(session).upsert(client_id=client.id)
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="api_client",
                entity_id=str(client.id),
                action=AuditAction.CREATE.value,
                new_value={"client_id": client_id, "name": name},
            )
            return ApiGatewayEngineV1._client_snapshot(client)

    @staticmethod
    async def create_api_key(
        actor_id: int,
        client_uuid: uuid.UUID,
        *,
        name: str,
        permissions: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> dict[str, Any]:
        if not await ApiGatewayEngineV1.user_can_access(actor_id):
            raise ApiGatewayEngineError("Access denied")

        raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:16]
        key_hash = ApiGatewayEngineV1._hash_key(raw_key)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        )

        async with get_session() as session:
            client = await ApiClientRepository(session).get_by_id(client_uuid)
            if client is None:
                raise ApiGatewayEngineError(f"Client not found: {client_uuid}")

            key = await ApiKeyRepository(session).create(
                client_id=client.id,
                name=name,
                key_prefix=key_prefix,
                key_hash=key_hash,
                permissions=permissions,
                expires_at=expires_at,
            )

            snapshot = ApiGatewayEngineV1._key_snapshot(key)
            snapshot["api_key"] = raw_key
            return snapshot

    @staticmethod
    async def authenticate_api_key(raw_key: str) -> ApiAuthContext:
        if not raw_key.startswith(API_KEY_PREFIX):
            raise ApiAuthenticationError("Invalid API key format")

        key_prefix = raw_key[:16]
        key_hash = ApiGatewayEngineV1._hash_key(raw_key)

        async with get_session() as session:
            candidates = await ApiKeyRepository(session).get_by_prefix(key_prefix)
            matched = None
            for candidate in candidates:
                if hmac.compare_digest(candidate.key_hash, key_hash):
                    matched = candidate
                    break

            if matched is None:
                raise ApiAuthenticationError("Invalid API key")

            if matched.status != ApiKeyStatus.ACTIVE.value:
                raise ApiAuthenticationError("API key revoked or expired")

            if matched.expires_at and matched.expires_at < datetime.now(timezone.utc):
                raise ApiAuthenticationError("API key expired")

            client = await ApiClientRepository(session).get_by_id(matched.client_id)
            if client is None or client.status != ApiClientStatus.ACTIVE.value:
                raise ApiAuthenticationError("API client inactive")

            await ApiKeyRepository(session).mark_used(matched.id)

            return ApiAuthContext(
                client_id=client.id,
                client_code=client.client_id,
                permissions=ApiGatewayEngineV1._resolve_permissions(client, matched),
                key_id=matched.id,
                actor_user_id=client.owner_user_id or OWNER_ID,
                auth_method="api_key",
            )

    @staticmethod
    def issue_jwt(
        client_code: str,
        client_uuid: uuid.UUID,
        permissions: set[str],
        *,
        ttl_hours: int | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": client_code,
            "cid": str(client_uuid),
            "permissions": sorted(permissions),
            "iat": now,
            "exp": now + timedelta(hours=ttl_hours or API_JWT_TTL_HOURS),
            "ver": "v1",
        }
        return jwt.encode(payload, API_JWT_SECRET, algorithm=API_JWT_ALGORITHM)

    @staticmethod
    async def authenticate_jwt(token: str) -> ApiAuthContext:
        try:
            payload = jwt.decode(
                token,
                API_JWT_SECRET,
                algorithms=[API_JWT_ALGORITHM],
            )
        except jwt.PyJWTError as exc:
            raise ApiAuthenticationError("Invalid or expired JWT") from exc

        client_code = payload.get("sub")
        client_uuid_str = payload.get("cid")
        if not client_code or not client_uuid_str:
            raise ApiAuthenticationError("Malformed JWT payload")

        async with get_session() as session:
            client = await ApiClientRepository(session).get_by_client_id(client_code)
            if client is None or client.status != ApiClientStatus.ACTIVE.value:
                raise ApiAuthenticationError("API client inactive")

            if str(client.id) != client_uuid_str:
                raise ApiAuthenticationError("JWT client mismatch")

            permissions = set(payload.get("permissions") or [])
            if not permissions:
                permissions = ApiGatewayEngineV1._resolve_permissions(client)

            return ApiAuthContext(
                client_id=client.id,
                client_code=client.client_id,
                permissions=permissions,
                actor_user_id=client.owner_user_id or OWNER_ID,
                auth_method="jwt",
            )

    @staticmethod
    async def authenticate_request(
        *,
        authorization: str | None = None,
        api_key_header: str | None = None,
    ) -> ApiAuthContext:
        if api_key_header:
            return await ApiGatewayEngineV1.authenticate_api_key(api_key_header)

        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
            if token.startswith(API_KEY_PREFIX):
                return await ApiGatewayEngineV1.authenticate_api_key(token)
            return await ApiGatewayEngineV1.authenticate_jwt(token)

        raise ApiAuthenticationError("Missing authentication credentials")

    @staticmethod
    async def check_rate_limit(
        ctx: ApiAuthContext,
        *,
        method: str,
        path: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            limit = await ApiRateLimitRepository(session).get_for_client(ctx.client_id)
            if limit is None:
                return

            usage_repo = ApiUsageLogRepository(session)
            minute_count = await usage_repo.count_since(
                client_id=ctx.client_id,
                key_id=ctx.key_id,
                since=now - timedelta(minutes=1),
            )
            hour_count = await usage_repo.count_since(
                client_id=ctx.client_id,
                key_id=ctx.key_id,
                since=now - timedelta(hours=1),
            )

            if minute_count >= limit.requests_per_minute:
                raise ApiRateLimitError(
                    f"Rate limit exceeded: {limit.requests_per_minute}/min"
                )
            if hour_count >= limit.requests_per_hour:
                raise ApiRateLimitError(
                    f"Rate limit exceeded: {limit.requests_per_hour}/hour"
                )

    @staticmethod
    def check_permission(ctx: ApiAuthContext, method: str, path: str) -> None:
        required = ApiGatewayEngineV1.required_permission(method, path)
        if required is None:
            return
        if required not in ctx.permissions and "api.admin" not in ctx.permissions:
            raise ApiPermissionError(f"Missing permission: {required}")

    @staticmethod
    async def log_request(
        *,
        ctx: ApiAuthContext | None,
        method: str,
        path: str,
        status_code: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        duration_ms: int | None = None,
        error_message: str | None = None,
    ) -> None:
        async with get_session() as session:
            await ApiUsageLogRepository(session).record(
                client_id=ctx.client_id if ctx else None,
                key_id=ctx.key_id if ctx else None,
                method=method,
                path=path,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                duration_ms=duration_ms,
                error_message=error_message,
            )

            if ctx and status_code < 500:
                await AuditRepository(session).create_log(
                    user_id=ctx.actor_user_id,
                    entity_type="api_request",
                    entity_id=request_id or path,
                    action=AuditAction.CREATE.value,
                    new_value={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "client": ctx.client_code,
                        "auth_method": ctx.auth_method,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

    @staticmethod
    async def exchange_api_key_for_jwt(raw_key: str) -> dict[str, Any]:
        ctx = await ApiGatewayEngineV1.authenticate_api_key(raw_key)
        token = ApiGatewayEngineV1.issue_jwt(
            ctx.client_code,
            ctx.client_id,
            ctx.permissions,
        )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": API_JWT_TTL_HOURS * 3600,
            "permissions": sorted(ctx.permissions),
        }

    @staticmethod
    async def get_usage_logs(
        actor_id: int,
        client_uuid: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await ApiGatewayEngineV1.user_can_access(actor_id):
            raise ApiGatewayEngineError("Access denied")

        async with get_session() as session:
            logs = await ApiUsageLogRepository(session).list_by_client(
                client_uuid,
                limit=limit,
            )
            return [
                {
                    "id": str(log.id),
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "duration_ms": log.duration_ms,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
