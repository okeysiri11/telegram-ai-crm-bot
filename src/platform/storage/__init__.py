# Platform storage interfaces — scaffold.
# TelegramStorage implemented. Local/S3 prepared.
# Parallel to services/storage — not replacing production wiring.

from __future__ import annotations

import abc
import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class StoredMedia:
    file_id: str | None = None
    cdn_url: str | None = None
    local_path: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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
        return StoredMedia(file_id=file_id, content_type=content_type, metadata=metadata or {})

    async def resolve_url(self, media: StoredMedia) -> str | None:
        return media.cdn_url or media.file_id

    async def delete(self, media: StoredMedia) -> bool:
        return True


class LocalStorage(StorageProvider):
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("LOCAL_STORAGE_DIR", "data/media_cache"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cdn_base = os.getenv("MEDIA_CDN_BASE_URL", "").rstrip("/")

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
        path = self.base_dir / f"{digest}_{filename or 'blob.bin'}"
        path.write_bytes(data)
        cdn = urljoin(self.cdn_base + "/", path.name) if self.cdn_base else None
        return StoredMedia(
            file_id=file_id,
            local_path=str(path),
            cdn_url=cdn,
            content_type=content_type,
            size_bytes=len(data),
            metadata=metadata or {},
        )

    async def resolve_url(self, media: StoredMedia) -> str | None:
        return media.cdn_url or media.local_path

    async def delete(self, media: StoredMedia) -> bool:
        if media.local_path and Path(media.local_path).exists():
            Path(media.local_path).unlink(missing_ok=True)
            return True
        return False


class S3Storage(StorageProvider):
    """Prepared stub — requires boto3 + S3_* env for production use."""

    def __init__(self) -> None:
        self.bucket = os.getenv("S3_BUCKET", "")

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
            logger.warning("S3Storage stub: S3_BUCKET not set — returning metadata only")
            return StoredMedia(
                file_id=file_id,
                s3_key=f"media/{filename or 'blob'}",
                content_type=content_type,
                size_bytes=len(data),
                metadata={**(metadata or {}), "stub": True},
            )
        # Full upload path is prepared in services/storage S3Storage when boto3 available.
        return StoredMedia(
            file_id=file_id,
            s3_key=f"media/{filename or 'blob'}",
            s3_url=f"s3://{self.bucket}/media/{filename or 'blob'}",
            content_type=content_type,
            size_bytes=len(data),
            metadata=metadata or {},
        )

    async def resolve_url(self, media: StoredMedia) -> str | None:
        return media.cdn_url or media.s3_url

    async def delete(self, media: StoredMedia) -> bool:
        return False


def get_storage_provider() -> StorageProvider:
    provider = os.getenv("MEDIA_STORAGE_PROVIDER", "telegram").strip().lower()
    if provider == "local":
        return LocalStorage()
    if provider == "s3":
        return S3Storage()
    return TelegramStorage()
