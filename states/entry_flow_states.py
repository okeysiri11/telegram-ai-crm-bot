# FSM states for entry-point flows.

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AutoClientFlow(StatesGroup):
    language_select = State()
    menu = State()
    awaiting_description = State()
    awaiting_photo = State()
    awaiting_listing_description = State()


class AutoDealerFlow(StatesGroup):
    language_select = State()
    dealer_onboarding = State()
