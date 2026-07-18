# Media storage providers — Telegram / Local / S3 / CDN.

from __future__ import annotations

import abc
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from config import (
    LOCAL_STORAGE_DIR,
    MEDIA_CDN_BASE_URL,
    MEDIA_LOCAL_CACHE,
    MEDIA_STORAGE_PROVIDER,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_ENDPOINT_URL,
    S3_REGION,
    S3_SECRET_KEY,
)

logger = logging.getLogger(__name__)


@dataclass
class StoredMedia:
    """Canonical representation of stored media."""

    file_id: str | None = None
    cdn_url: str | None = None
    local_path: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "cdn_url": self.cdn_url,
            "local_path": self.local_path,
            "s3_key": self.s3_key,
            "s3_url": self.s3_url,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }


class StorageProvider(abc.ABC):
    @abc.abstractmethod
    async def store(
        self,
        *,
        data: bytes | None = None,
        file_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        ...

    @abc.abstractmethod
    async def resolve_url(self, media: StoredMedia) -> str | None:
        ...

    @abc.abstractmethod
    async def delete(self, media: StoredMedia) -> bool:
        ...


class TelegramStorage(StorageProvider):
    """Keeps Telegram file_id as primary reference."""

    async def store(
        self,
        *,
        data: bytes | None = None,
        file_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        if not file_id:
            raise ValueError("TelegramStorage requires file_id")
        return StoredMedia(
            file_id=file_id,
            content_type=content_type,
            metadata=metadata or {},
        )

    async def resolve_url(self, media: StoredMedia) -> str | None:
        return media.cdn_url or media.file_id

    async def delete(self, media: StoredMedia) -> bool:
        return True


class LocalStorage(StorageProvider):
    """Caches binary blobs on local filesystem."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or LOCAL_STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cdn_base = MEDIA_CDN_BASE_URL.rstrip("/")

    async def store(
        self,
        *,
        data: bytes | None = None,
        file_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        if data is None:
            return StoredMedia(file_id=file_id, content_type=content_type, metadata=metadata or {})

        digest = hashlib.sha256(data).hexdigest()[:16]
        safe_name = filename or f"{digest}.bin"
        path = self.base_dir / f"{digest}_{safe_name}"
        path.write_bytes(data)

        cdn_url = None
        if self.cdn_base:
            cdn_url = urljoin(self.cdn_base + "/", path.name)

        return StoredMedia(
            file_id=file_id,
            local_path=str(path),
            cdn_url=cdn_url,
            content_type=content_type,
            size_bytes=len(data),
            metadata=metadata or {},
        )

    async def resolve_url(self, media: StoredMedia) -> str | None:
        if media.cdn_url:
            return media.cdn_url
        return media.local_path

    async def delete(self, media: StoredMedia) -> bool:
        if media.local_path and Path(media.local_path).exists():
            Path(media.local_path).unlink(missing_ok=True)
            return True
        return False


class S3Storage(StorageProvider):
    """S3-compatible object storage (boto3 optional)."""

    def __init__(self) -> None:
        self.bucket = S3_BUCKET
        self.region = S3_REGION
        self.endpoint = S3_ENDPOINT_URL
        self.cdn_base = MEDIA_CDN_BASE_URL.rstrip("/")
        self.access_key = S3_ACCESS_KEY
        self.secret_key = S3_SECRET_KEY

    def _client(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3Storage") from exc
        kwargs: dict[str, Any] = {
            "region_name": self.region,
            "aws_access_key_id": self.access_key or None,
            "aws_secret_access_key": self.secret_key or None,
        }
        if self.endpoint:
            kwargs["endpoint_url"] = self.endpoint
        return boto3.client("s3", **kwargs)

    async def store(
        self,
        *,
        data: bytes | None = None,
        file_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        if data is None:
            return StoredMedia(file_id=file_id, content_type=content_type, metadata=metadata or {})
        if not self.bucket:
            raise RuntimeError("S3_BUCKET is not configured")

        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"media/{digest}_{filename or 'blob'}"
        client = self._client()
        extra: dict[str, Any] = {}
        if content_type:
            extra["ContentType"] = content_type
        client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)

        s3_url = f"s3://{self.bucket}/{key}"
        cdn_url = urljoin(self.cdn_base + "/", key) if self.cdn_base else None
        return StoredMedia(
            file_id=file_id,
            s3_key=key,
            s3_url=s3_url,
            cdn_url=cdn_url,
            content_type=content_type,
            size_bytes=len(data),
            metadata=metadata or {},
        )

    async def resolve_url(self, media: StoredMedia) -> str | None:
        if media.cdn_url:
            return media.cdn_url
        return media.s3_url

    async def delete(self, media: StoredMedia) -> bool:
        if not media.s3_key or not self.bucket:
            return False
        try:
            self._client().delete_object(Bucket=self.bucket, Key=media.s3_key)
            return True
        except Exception:
            logger.exception("S3 delete failed key=%s", media.s3_key)
            return False


class CompositeStorage(StorageProvider):
    """Primary provider + optional local cache + CDN URL enrichment."""

    def __init__(self, primary: StorageProvider, cache: LocalStorage | None = None) -> None:
        self.primary = primary
        self.cache = cache

    async def store(
        self,
        *,
        data: bytes | None = None,
        file_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        media = await self.primary.store(
            data=data,
            file_id=file_id,
            filename=filename,
            content_type=content_type,
            metadata=metadata,
        )
        if data is not None and self.cache is not None:
            cached = await self.cache.store(
                data=data,
                file_id=file_id or media.file_id,
                filename=filename,
                content_type=content_type,
                metadata=metadata,
            )
            media.local_path = cached.local_path
            media.cdn_url = media.cdn_url or cached.cdn_url
            media.size_bytes = media.size_bytes or cached.size_bytes
        return media

    async def resolve_url(self, media: StoredMedia) -> str | None:
        return await self.primary.resolve_url(media)

    async def delete(self, media: StoredMedia) -> bool:
        ok = await self.primary.delete(media)
        if self.cache:
            await self.cache.delete(media)
        return ok


def get_storage_provider() -> StorageProvider:
    """Factory switched by MEDIA_STORAGE_PROVIDER (telegram|local|s3)."""
    provider = MEDIA_STORAGE_PROVIDER.strip().lower()
    cache_enabled = MEDIA_LOCAL_CACHE
    cache = LocalStorage() if cache_enabled and provider != "local" else None

    if provider == "local":
        return LocalStorage()
    if provider == "s3":
        return CompositeStorage(S3Storage(), cache=cache)
    return CompositeStorage(TelegramStorage(), cache=cache)
