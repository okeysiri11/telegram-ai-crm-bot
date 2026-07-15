# FSM states for entry-point flows.

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AutoClientFlow(StatesGroup):
    language_select = State()
    menu = State()
    awaiting_description = State()
    awaiting_photo = State()
    awaiting_listing_description = State()
    awaiting_phone = State()
    services_hub = State()


# Persisted in user_vertical_preferences.onboarding_step (MemoryStorage FSM restore).
AUTO_CLIENT_PENDING_RESTORE: dict[str, tuple[State, str]] = {
    "ac:desc:buy_car": (AutoClientFlow.awaiting_description, "buy_car"),
    "ac:desc:sell_car": (AutoClientFlow.awaiting_description, "sell_car"),
    "ac:photo:listing": (AutoClientFlow.awaiting_photo, "listing"),
    "ac:ldsc:listing": (AutoClientFlow.awaiting_listing_description, "listing"),
    "ac:phone:manager": (AutoClientFlow.awaiting_phone, "manager_callback"),
    "ac:services:hub": (AutoClientFlow.services_hub, "services"),
}


class AutoDealerFlow(StatesGroup):
    language_select = State()
    dealer_onboarding = State()
