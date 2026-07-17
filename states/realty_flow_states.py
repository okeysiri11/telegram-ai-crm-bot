# FSM states for REALTY client flows.

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup

from services.realty_flow_engine import FLOW_STEPS, pending_key


class RealtyFlow(StatesGroup):
    menu = State()
    collecting = State()
    awaiting_photos = State()
    awaiting_contact = State()


def _build_pending_restore() -> dict[str, tuple[State, str | None]]:
    mapping: dict[str, tuple[State, str | None]] = {}
    for scenario, steps in FLOW_STEPS.items():
        for step in steps:
            key = pending_key(scenario, step)
            if step == "photos":
                mapping[key] = (RealtyFlow.awaiting_photos, scenario)
            elif step == "contact":
                mapping[key] = (RealtyFlow.awaiting_contact, scenario)
            else:
                mapping[key] = (RealtyFlow.collecting, scenario)
    return mapping


REALTY_PENDING_RESTORE: dict[str, tuple[State, str | None]] = _build_pending_restore()
