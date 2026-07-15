# Telegram media group photo collector — buffers album messages.

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from aiogram.types import Message

logger = logging.getLogger(__name__)


class PhotoAlbumCollector:
    """Collect photos from media groups; returns file_ids when album is complete."""

    def __init__(self, *, delay: float = 0.8) -> None:
        self._delay = delay
        self._pending: dict[str, list[str]] = defaultdict(list)
        self._tasks: dict[str, asyncio.Task] = {}

    async def add_photo(self, message: Message) -> list[str] | None:
        """Add photo from message. Returns complete album file_ids or None if still collecting."""
        if not message.photo:
            return None

        file_id = message.photo[-1].file_id
        group_id = message.media_group_id

        if not group_id:
            return [file_id]

        key = f"{message.chat.id}:{group_id}"
        self._pending[key].append(file_id)

        if key in self._tasks:
            self._tasks[key].cancel()

        loop = asyncio.get_running_loop()
        task = loop.create_task(self._finalize(key))
        self._tasks[key] = task

        try:
            return await task
        except asyncio.CancelledError:
            return None

    async def _finalize(self, key: str) -> list[str]:
        await asyncio.sleep(self._delay)
        photos = self._pending.pop(key, [])
        self._tasks.pop(key, None)
        logger.debug("Photo album collected key=%s count=%s", key, len(photos))
        return photos


photo_album_collector = PhotoAlbumCollector()
