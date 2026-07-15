# FSM states for entry-point flows.

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AutoClientFlow(StatesGroup):
    language_select = State()
    menu = State()
    collecting = State()
    awaiting_photos = State()
    awaiting_vin = State()
    awaiting_phone = State()
    services_hub = State()


def _build_pending_restore() -> dict[str, tuple[State, str]]:
    from services.auto_client_flow_engine import FLOW_STEPS, pending_key

    mapping: dict[str, tuple[State, str]] = {}
    for flow_type, steps in FLOW_STEPS.items():
        for step in steps:
            if step == "photos":
                fsm_state = AutoClientFlow.awaiting_photos
            elif step == "vin_optional":
                fsm_state = AutoClientFlow.awaiting_vin
            elif step == "phone":
                fsm_state = AutoClientFlow.awaiting_phone
            else:
                fsm_state = AutoClientFlow.collecting
            mapping[pending_key(flow_type, step)] = (fsm_state, flow_type)
    mapping["ac:services:hub"] = (AutoClientFlow.services_hub, "services")
    return mapping


AUTO_CLIENT_PENDING_RESTORE: dict[str, tuple[State, str]] = _build_pending_restore()
