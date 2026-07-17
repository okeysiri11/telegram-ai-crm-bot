# MediaService — file and photo storage (delegates to platform storage).

from __future__ import annotations

from typing import Any


class MediaService:
    @staticmethod
    async def store_telegram_file(
        *,
        file_id: str,
        destination: str | None = None,
    ) -> dict[str, Any]:
        from src.platform.storage import get_storage_provider

        storage = get_storage_provider()
        if hasattr(storage, "store_telegram_file"):
            return await storage.store_telegram_file(file_id=file_id, destination=destination)
        return {"file_id": file_id, "stored": False, "reason": "provider_has_no_telegram_store"}

    @staticmethod
    async def store_local(path: str, data: bytes) -> dict[str, Any]:
        from src.platform.storage import LocalStorage

        storage = LocalStorage()
        if hasattr(storage, "write"):
            await storage.write(path, data)
            return {"path": path, "stored": True}
        return {"path": path, "stored": False}

    @staticmethod
    def resolve_photo_file_ids(primary: str | None, extras: list[str] | None = None) -> list[str]:
        ids: list[str] = []
        if primary:
            ids.append(primary)
        for fid in extras or []:
            if fid and fid not in ids:
                ids.append(fid)
        return ids


media_service = MediaService()
