"""FSM states for Telegram AI Super App — Sprint 43.3 / 43.4."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SuperAppFlow(StatesGroup):
    concierge_chat = State()
    studio_step = State()
    awaiting_free_text = State()
    clarify_chat = State()
    await_generate_confirm = State()
    ask_ai = State()
    vertical_menu = State()
    vertical_wizard = State()
    vertical_confirm = State()
