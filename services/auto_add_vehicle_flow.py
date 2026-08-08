"""HOTFIX 46.2.2 — Canonical Auto Add Vehicle FSM (durable, AI-safe).

Architectural invariants:
- Active AUTO_ADD_VEHICLE FSM must never reach general AI / intent routers.
- Optional fields (VIN, photo, color, mileage, costs) never block create.
- State lives in aiogram FSM storage (Redis in production), not only process memory.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram.fsm.context import FSMContext

from states.entry_flow_states import AutoAddVehicleFlow

logger = logging.getLogger(__name__)

FLOW_NAME = "AUTO_ADD_VEHICLE"

# Map FSM state → logical active_state label
STATE_LABELS: dict[str, str] = {
    AutoAddVehicleFlow.make.state: "MAKE",
    AutoAddVehicleFlow.model.state: "MODEL",
    AutoAddVehicleFlow.year.state: "YEAR",
    AutoAddVehicleFlow.color.state: "COLOR",
    AutoAddVehicleFlow.mileage.state: "MILEAGE",
    AutoAddVehicleFlow.purchase_price.state: "PURCHASE_PRICE",
    AutoAddVehicleFlow.optional_costs.state: "OPTIONAL_COSTS",
    AutoAddVehicleFlow.vin_decision.state: "VIN_DECISION",
    AutoAddVehicleFlow.waiting_vin.state: "WAITING_VIN",
    AutoAddVehicleFlow.finalize_retry.state: "FINALIZE_RETRY",
}

STEP_TO_STATE = {
    "make": AutoAddVehicleFlow.make,
    "model": AutoAddVehicleFlow.model,
    "year": AutoAddVehicleFlow.year,
    "color": AutoAddVehicleFlow.color,
    "mileage": AutoAddVehicleFlow.mileage,
    "purchase_price": AutoAddVehicleFlow.purchase_price,
    "optional_costs": AutoAddVehicleFlow.optional_costs,
    "vin_optional": AutoAddVehicleFlow.vin_decision,
    "vin_decision": AutoAddVehicleFlow.vin_decision,
    "vin_input": AutoAddVehicleFlow.waiting_vin,
    "waiting_vin": AutoAddVehicleFlow.waiting_vin,
    "finalize_retry": AutoAddVehicleFlow.finalize_retry,
}


class ActiveFlowRoutingRequired(RuntimeError):
    """Raised when general AI router receives an update while Add-car FSM is active."""

    def __init__(self, user_id: int | None = None, active_state: str | None = None) -> None:
        self.user_id = user_id
        self.active_state = active_state
        super().__init__(
            f"ACTIVE_FLOW_ROUTING_REQUIRED user_id={user_id} active_state={active_state}"
        )


def is_auto_add_vehicle_state(state_name: str | None) -> bool:
    if not state_name:
        return False
    return state_name.startswith("AutoAddVehicleFlow:")


async def get_active_flow_snapshot(state: FSMContext) -> dict[str, Any]:
    current = await state.get_state()
    data = await state.get_data()
    label = STATE_LABELS.get(current or "", data.get("active_state"))
    return {
        "active_flow": data.get("active_flow") if is_auto_add_vehicle_state(current) else None,
        "active_state": label if is_auto_add_vehicle_state(current) else None,
        "fsm_state": current,
        "draft": dict(data.get("draft") or {}) if is_auto_add_vehicle_state(current) else {},
    }


async def has_active_add_vehicle_flow(state: FSMContext | None) -> bool:
    if state is None:
        return False
    current = await state.get_state()
    if is_auto_add_vehicle_state(current):
        return True
    data = await state.get_data()
    return data.get("active_flow") == FLOW_NAME and bool(data.get("active_state"))


async def assert_no_active_add_vehicle(state: FSMContext | None, *, user_id: int | None = None) -> None:
    """Hard guard for general AI / intent routers."""
    if not await has_active_add_vehicle_flow(state):
        return
    snap = await get_active_flow_snapshot(state) if state else {}
    logger.error(
        "ACTIVE_FLOW_ROUTING_REQUIRED blocked AI router user_id=%s active_state=%s",
        user_id,
        snap.get("active_state"),
    )
    raise ActiveFlowRoutingRequired(user_id=user_id, active_state=snap.get("active_state"))


async def persist_add_vehicle(
    state: FSMContext,
    *,
    step: str,
    draft: dict[str, Any],
) -> None:
    fsm_state = STEP_TO_STATE.get(step)
    if fsm_state is None:
        raise ValueError(f"unknown add-vehicle step: {step}")
    label = STATE_LABELS.get(fsm_state.state, step.upper())
    await state.set_state(fsm_state)
    await state.update_data(
        active_flow=FLOW_NAME,
        active_state=label,
        draft=dict(draft),
    )
    logger.info(
        "TELEGRAM_UPDATE active_flow=%s active_state=%s draft_keys=%s",
        FLOW_NAME,
        label,
        sorted(draft.keys()),
    )


async def clear_add_vehicle(state: FSMContext) -> None:
    await state.update_data(active_flow=None, active_state=None, draft={})
    current = await state.get_state()
    if is_auto_add_vehicle_state(current):
        await state.set_state(None)


def format_vehicle_created_ru(draft: dict[str, Any], *, vin: str | None) -> str:
    make = draft.get("make") or "Авто"
    model = draft.get("model") or "—"
    year = draft.get("year") or "—"
    fields = draft.get("fields") or {}
    purchase = fields.get("purchase_price")
    if purchase is not None:
        try:
            price_s = f"${int(float(purchase)):,}".replace(",", " ")
        except (TypeError, ValueError):
            price_s = str(purchase)
    else:
        price_s = "не указана"
    vin_line = vin if vin else "не указан"
    return (
        f"✅ Автомобиль добавлен.\n\n"
        f"{make} {model} · {year}\n"
        f"Закупка: {price_s}\n"
        f"VIN: {vin_line}"
    )


def mirror_process_flow(user_id: int, step: str, draft: dict[str, Any]) -> None:
    """Keep legacy in-process dict in sync for readiness probes (source of truth = FSM)."""
    try:
        import auto_vertical_handlers as avh

        avh.auto_vertical_active[user_id] = True
        avh.auto_vertical_section[user_id] = "cars"
        avh.auto_vertical_flow[user_id] = {"step": step, "data": dict(draft)}
    except Exception:
        logger.debug("mirror_process_flow skipped", exc_info=True)


def clear_process_flow(user_id: int) -> None:
    try:
        import auto_vertical_handlers as avh

        avh.auto_vertical_flow.pop(user_id, None)
    except Exception:
        pass
