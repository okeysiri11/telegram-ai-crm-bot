# Entry point middleware — reject cross-flow navigation.

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.pg_entry_point_engine import EntryPointEngineV1
from services.entry_point_routing import EntryPoint, FlowState
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AUTO_CLIENT_PENDING_RESTORE, AutoClientFlow


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

        state = data.get("state")
        if state is not None:
            ctx = await EntryPointEngineV1.get_flow_context(user_id)
            if ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value or ctx.get("source_link") == "auto_client":
                fsm_state = await state.get_state()
                if fsm_state is None:
                    pending = await VerticalOnboardingEngineV1.get_auto_client_pending(user_id)
                    mapping = AUTO_CLIENT_PENDING_RESTORE.get(pending or "")
                    if mapping is not None:
                        await state.set_state(mapping[0])
                        if mapping[1] != "services":
                            await state.update_data(request_type=mapping[1])
                    elif ctx.get("current_flow") == FlowState.AUTO_CLIENT_MENU.value:
                        await state.set_state(AutoClientFlow.menu)

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
