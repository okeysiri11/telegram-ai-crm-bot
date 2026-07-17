# Error tracking middleware — capture handler failures without breaking polling.

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.error_tracking_service import error_tracking_service

logger = logging.getLogger(__name__)

_USER_MESSAGE = "Произошла ошибка. Мы уже получили уведомление и работаем над исправлением."


class ErrorTrackingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            try:
                await error_tracking_service.track_from_handler(exc, event, data)
            except Exception:
                logger.warning("Error tracking failed", exc_info=True)

            try:
                await _notify_user(event)
            except Exception:
                logger.debug("Failed to notify user about handler error", exc_info=True)

            return None


async def _notify_user(event: TelegramObject) -> None:
    if isinstance(event, Message):
        await event.answer(_USER_MESSAGE)
    elif isinstance(event, CallbackQuery):
        if event.message is not None:
            await event.message.answer(_USER_MESSAGE)
        await event.answer("Ошибка", show_alert=False)
