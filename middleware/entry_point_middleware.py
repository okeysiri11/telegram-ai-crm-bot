# Entry point middleware — reject cross-flow navigation.

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.pg_entry_point_engine import EntryPointEngineV1


class EntryPointMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if EntryPointEngineV1.is_exempt_event(event):
            return await handler(event, data)

        user_id = None
        text = None
        callback_data = None
        answer_target = None

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            text = event.text
            answer_target = event
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            callback_data = event.data
            answer_target = event.message

        if user_id is None:
            return await handler(event, data)

        denial = await EntryPointEngineV1.check_transition(
            user_id,
            text=text,
            callback_data=callback_data,
        )
        if denial and answer_target is not None:
            markup = await EntryPointEngineV1.reply_markup_for_user(user_id)
            await answer_target.answer(denial, reply_markup=markup)
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        return await handler(event, data)
