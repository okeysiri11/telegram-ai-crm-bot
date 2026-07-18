# API keys — create, rotate, disable, scoped permissions.

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from platform_identity.exceptions import ApiKeyError
from platform_identity.models import ApiKeyRecord, Principal, PlatformRole, AuthMethod

logger = logging.getLogger(__name__)

KEY_PREFIX = "iam_live_"


class ApiKeyService:
    def __init__(self) -> None:
        self._keys: dict[str, ApiKeyRecord] = {}
        self._hash_index: dict[str, str] = {}

    def reset(self) -> None:
        self._keys.clear()
        self._hash_index.clear()

    def create_key(
        self,
        *,
        name: str,
        scopes: list[str],
        telegram_id: int | None = None,
        expires_in_days: int | None = 365,
        roles: list[str] | None = None,
    ) -> tuple[str, ApiKeyRecord]:
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        key_hash = self._hash(raw)
        key_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = (
            now + timedelta(days=expires_in_days) if expires_in_days is not None else None
        )

        principal_id = f"apikey:{key_id}"
        record = ApiKeyRecord(
            key_id=key_id,
            name=name,
            key_hash=key_hash,
            prefix=raw[:12] + "...",
            scopes=scopes,
            created_at=now,
            expires_at=expires_at,
            principal_id=principal_id,
            telegram_id=telegram_id,
        )
        self._keys[key_id] = record
        self._hash_index[key_hash] = key_id
        logger.info("iam_api_key_created id=%s name=%s", key_id, name)
        return raw, record

    def rotate_key(self, key_id: str) -> tuple[str, ApiKeyRecord]:
        existing = self._keys.get(key_id)
        if existing is None:
            raise ApiKeyError(f"API key {key_id} not found")
        if existing.disabled:
            raise ApiKeyError(f"API key {key_id} is disabled")

        self.disable_key(key_id)
        return self.create_key(
            name=f"{existing.name} (rotated)",
            scopes=list(existing.scopes),
            telegram_id=existing.telegram_id,
            expires_in_days=None if existing.expires_at is None else 365,
        )

    def disable_key(self, key_id: str) -> ApiKeyRecord:
        record = self._keys.get(key_id)
        if record is None:
            raise ApiKeyError(f"API key {key_id} not found")
        record.disabled = True
        return record

    def list_keys(self) -> list[ApiKeyRecord]:
        return list(self._keys.values())

    def get_key(self, key_id: str) -> ApiKeyRecord:
        record = self._keys.get(key_id)
        if record is None:
            raise ApiKeyError(f"API key {key_id} not found")
        return record

    async def authenticate(self, raw_key: str) -> Principal:
        key_hash = self._hash(raw_key)
        key_id = self._hash_index.get(key_hash)
        if key_id is None:
            raise ApiKeyError("Invalid API key")

        record = self._keys[key_id]
        if record.disabled:
            raise ApiKeyError("API key disabled")

        now = datetime.now(timezone.utc)
        if record.expires_at is not None and now > record.expires_at:
            raise ApiKeyError("API key expired")

        record.last_used_at = now

        from platform_identity.audit_hooks import iam_audit

        await iam_audit.log_api_key_usage(record)

        roles = [PlatformRole.SERVICE.value]
        if record.telegram_id is not None:
            from platform_identity.role_service import role_service

            roles = await role_service.roles_for_telegram_user(record.telegram_id)

        return Principal(
            principal_id=record.principal_id or f"apikey:{record.key_id}",
            auth_method=AuthMethod.API_KEY,
            roles=roles,
            permissions=list(record.scopes),
            telegram_id=record.telegram_id,
            api_key_id=record.key_id,
        )

    @staticmethod
    def _hash(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()


api_key_service = ApiKeyService()
