# Public API Gateway v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.api_gateway import (
    ApiClient,
    ApiClientStatus,
    ApiKey,
    ApiKeyStatus,
    ApiRateLimit,
    ApiUsageLog,
)


class ApiClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: str,
        name: str,
        permissions: list[str] | None = None,
        description: str | None = None,
        owner_user_id: int | None = None,
        metadata: dict | None = None,
        status: str = ApiClientStatus.ACTIVE.value,
        **extra: Any,
    ) -> ApiClient:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        client = ApiClient(
            client_id=client_id,
            name=name,
            permissions=permissions,
            description=description,
            owner_user_id=owner_user_id,
            metadata_=metadata,
            status=status,
        )
        self._session.add(client)
        await self._session.flush()
        return client

    async def get_by_id(self, id_: uuid.UUID) -> ApiClient | None:
        result = await self._session.execute(
            select(ApiClient).where(ApiClient.id == id_)
        )
        return result.scalar_one_or_none()

    async def get_by_client_id(self, client_id: str) -> ApiClient | None:
        result = await self._session.execute(
            select(ApiClient).where(ApiClient.client_id == client_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ApiClient]:
        result = await self._session.execute(
            select(ApiClient)
            .where(ApiClient.status == ApiClientStatus.ACTIVE.value)
            .order_by(ApiClient.name.asc())
        )
        return list(result.scalars().all())


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: uuid.UUID,
        name: str,
        key_prefix: str,
        key_hash: str,
        permissions: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> ApiKey:
        key = ApiKey(
            client_id=client_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=expires_at,
        )
        self._session.add(key)
        await self._session.flush()
        return key

    async def get_by_id(self, key_id: uuid.UUID) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_prefix(self, key_prefix: str) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == key_prefix,
                ApiKey.status == ApiKeyStatus.ACTIVE.value,
            )
        )
        return list(result.scalars().all())

    async def mark_used(self, key_id: uuid.UUID) -> None:
        key = await self.get_by_id(key_id)
        if key is None:
            return
        key.last_used_at = datetime.now(timezone.utc)
        key.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def revoke(self, key_id: uuid.UUID) -> ApiKey | None:
        key = await self.get_by_id(key_id)
        if key is None:
            return None
        key.status = ApiKeyStatus.REVOKED.value
        key.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return key

    async def list_by_client(self, client_id: uuid.UUID) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKey)
            .where(ApiKey.client_id == client_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())


class ApiUsageLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        client_id: uuid.UUID | None = None,
        key_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        duration_ms: int | None = None,
        api_version: str = "v1",
        error_message: str | None = None,
    ) -> ApiUsageLog:
        log = ApiUsageLog(
            client_id=client_id,
            key_id=key_id,
            method=method,
            path=path,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            duration_ms=duration_ms,
            api_version=api_version,
            error_message=error_message,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def count_since(
        self,
        *,
        client_id: uuid.UUID,
        since: datetime,
        key_id: uuid.UUID | None = None,
    ) -> int:
        query = select(func.count()).select_from(ApiUsageLog).where(
            ApiUsageLog.client_id == client_id,
            ApiUsageLog.created_at >= since,
        )
        if key_id is not None:
            query = query.where(ApiUsageLog.key_id == key_id)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_by_client(
        self,
        client_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[ApiUsageLog]:
        result = await self._session.execute(
            select(ApiUsageLog)
            .where(ApiUsageLog.client_id == client_id)
            .order_by(ApiUsageLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ApiRateLimitRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        endpoint_pattern: str = "*",
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        client_id: uuid.UUID | None = None,
        key_id: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> ApiRateLimit:
        query = select(ApiRateLimit).where(
            ApiRateLimit.endpoint_pattern == endpoint_pattern,
            ApiRateLimit.client_id == client_id,
            ApiRateLimit.key_id == key_id,
        )
        result = await self._session.execute(query)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.requests_per_minute = requests_per_minute
            existing.requests_per_hour = requests_per_hour
            existing.burst_limit = burst_limit
            existing.is_active = is_active
            existing.updated_at = datetime.now(timezone.utc)
            await self._session.flush()
            return existing

        limit = ApiRateLimit(
            client_id=client_id,
            key_id=key_id,
            endpoint_pattern=endpoint_pattern,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_limit=burst_limit,
            is_active=is_active,
        )
        self._session.add(limit)
        await self._session.flush()
        return limit

    async def get_for_client(
        self,
        client_id: uuid.UUID,
        endpoint_pattern: str = "*",
    ) -> ApiRateLimit | None:
        result = await self._session.execute(
            select(ApiRateLimit)
            .where(
                ApiRateLimit.client_id == client_id,
                ApiRateLimit.endpoint_pattern == endpoint_pattern,
                ApiRateLimit.is_active.is_(True),
            )
            .limit(1)
        )
        specific = result.scalar_one_or_none()
        if specific is not None:
            return specific

        result = await self._session.execute(
            select(ApiRateLimit)
            .where(
                ApiRateLimit.client_id.is_(None),
                ApiRateLimit.endpoint_pattern == "*",
                ApiRateLimit.is_active.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
