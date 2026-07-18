# ManagerPoolService — dynamic manager assignment with configurable strategies.

from __future__ import annotations

import logging
import os
import random
import time
import uuid
from typing import Any

from config import (
    DEFAULT_AGRO_MANAGER_ID,
    DEFAULT_AUTO_MANAGER_ID,
    DEFAULT_DEALER_MANAGER_ID,
    DEFAULT_REALTY_MANAGER_ID,
    MANAGERS,
    OWNER_ID,
)
from database.session import get_session
from events.event_bus import publish
from events.manager_pool_events import (
    ManagerAssignedEvent,
    ManagerReleasedEvent,
    ManagerUnavailableEvent,
)
from models.manager_pool import AssignmentMode, ManagerPoolSnapshot
from repositories.manager_pool_repository import ManagerPoolRepository
from repositories.manager_repository import ManagerRepository
from repositories.user_repository import UserRepository
from services.system_roles import SystemRole, Vertical, normalize_vertical

logger = logging.getLogger(__name__)

NON_ASSIGNABLE_ROLES = frozenset({SystemRole.SUPER_ADMIN.value, "OWNER", "ADMIN"})

_ASSIGNMENT_MODE = os.getenv("MANAGER_ASSIGNMENT_MODE", AssignmentMode.ROUND_ROBIN.value).upper()
_assignment_latencies_ms: list[float] = []
_MAX_LATENCY_SAMPLES = 200


def _assignment_mode() -> AssignmentMode:
    try:
        return AssignmentMode(_ASSIGNMENT_MODE)
    except ValueError:
        logger.warning("Invalid MANAGER_ASSIGNMENT_MODE=%s — using ROUND_ROBIN", _ASSIGNMENT_MODE)
        return AssignmentMode.ROUND_ROBIN


def _record_latency_ms(duration_ms: float) -> None:
    _assignment_latencies_ms.append(duration_ms)
    if len(_assignment_latencies_ms) > _MAX_LATENCY_SAMPLES:
        del _assignment_latencies_ms[0 : len(_assignment_latencies_ms) - _MAX_LATENCY_SAMPLES]


class ManagerPoolService:
    @staticmethod
    def assignment_mode_name() -> str:
        return _assignment_mode().value

    @staticmethod
    async def bootstrap_from_config() -> dict[str, int]:
        """Seed manager_pool from subscriptions and env defaults (startup only)."""
        seeded = 0
        vertical_defaults: dict[str, list[tuple[int | None, str]]] = {
            Vertical.AUTO.value: [
                (DEFAULT_AUTO_MANAGER_ID, MANAGERS.get(DEFAULT_AUTO_MANAGER_ID or 0, "Auto Manager")),
                (DEFAULT_DEALER_MANAGER_ID, MANAGERS.get(DEFAULT_DEALER_MANAGER_ID or 0, "Dealer Manager")),
            ],
            Vertical.AGRO.value: [
                (DEFAULT_AGRO_MANAGER_ID, MANAGERS.get(DEFAULT_AGRO_MANAGER_ID or 0, "Agro Manager")),
            ],
            Vertical.REALTY.value: [
                (DEFAULT_REALTY_MANAGER_ID, MANAGERS.get(DEFAULT_REALTY_MANAGER_ID or 0, "Realty Manager")),
            ],
        }

        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            mgr_repo = ManagerRepository(session)

            for vertical in (Vertical.AUTO.value, Vertical.AGRO.value, Vertical.REALTY.value):
                for sub, user in await mgr_repo.list_subscribers(vertical):
                    if user.role in NON_ASSIGNABLE_ROLES or sub.role_code in NON_ASSIGNABLE_ROLES:
                        continue
                    if user.telegram_id is None or user.telegram_id == OWNER_ID:
                        continue
                    name = user.full_name or user.username or str(user.telegram_id)
                    await pool_repo.upsert_manager(
                        telegram_id=int(user.telegram_id),
                        name=name,
                        vertical=vertical,
                        priority=200 if sub.is_primary else 100,
                        weight=200 if sub.is_primary else 100,
                        is_active=True,
                    )
                    seeded += 1

                for tid, name in vertical_defaults.get(vertical, []):
                    if tid is None or tid == OWNER_ID:
                        continue
                    existing = await pool_repo.get_by_telegram_and_vertical(tid, vertical)
                    if existing is None:
                        await pool_repo.upsert_manager(
                            telegram_id=tid,
                            name=name,
                            vertical=vertical,
                            priority=150,
                            weight=150,
                            is_active=True,
                        )
                        seeded += 1

        logger.info("manager_pool_bootstrap complete seeded=%s", seeded)
        return {"seeded": seeded}

    @staticmethod
    def _select_manager(
        managers: list[ManagerPoolSnapshot],
        mode: AssignmentMode,
        *,
        exclude_telegram_ids: set[int] | None = None,
    ) -> ManagerPoolSnapshot | None:
        exclude = exclude_telegram_ids or set()
        candidates = [m for m in managers if m.telegram_id not in exclude]
        if not candidates:
            return None

        if mode == AssignmentMode.LEAST_LOADED:
            return sorted(
                candidates,
                key=lambda m: (m.current_load, -m.priority, m.last_assigned_at or ""),
            )[0]

        if mode == AssignmentMode.PRIORITY:
            return sorted(
                candidates,
                key=lambda m: (-m.priority, m.current_load, m.last_assigned_at or ""),
            )[0]

        if mode == AssignmentMode.WEIGHTED:
            weights = [max(1, m.weight) for m in candidates]
            return random.choices(candidates, weights=weights, k=1)[0]

        # ROUND_ROBIN — oldest last_assigned_at first (nulls first)
        return sorted(
            candidates,
            key=lambda m: (
                m.last_assigned_at is not None,
                m.last_assigned_at or "",
                m.current_load,
            ),
        )[0]

    @staticmethod
    async def _manager_snapshot_from_pool(
        entry: ManagerPoolSnapshot,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(entry.telegram_id)
            if user is None or user.telegram_id is None:
                return None
            snap = ManagerRepository.manager_snapshot(user)
            snap["pool_id"] = entry.id
            snap["vertical"] = entry.vertical
            snap["pool_load"] = entry.current_load
            return snap

    @staticmethod
    async def assign_manager(
        vertical: str,
        *,
        exclude_telegram_ids: set[int] | None = None,
        request_id: str | None = None,
        request_number: str | None = None,
        increment_load: bool = True,
    ) -> dict[str, Any] | None:
        started = time.monotonic()
        key = normalize_vertical(vertical) or vertical.strip().lower()
        mode = _assignment_mode()

        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            managers = await pool_repo.get_available_managers(key, for_update=True)
            picked = ManagerPoolService._select_manager(
                managers,
                mode,
                exclude_telegram_ids=exclude_telegram_ids,
            )
            if picked is None:
                await publish(
                    ManagerUnavailableEvent(
                        vertical=key,
                        reason="no_active_managers",
                        assignment_mode=mode.value,
                    )
                )
                return None

            updated = picked
            if increment_load:
                updated = await pool_repo.update_load(picked.id, delta=1) or picked
            updated = await pool_repo.touch_last_assigned(picked.id) or updated

        result = await ManagerPoolService._manager_snapshot_from_pool(updated)
        if result is None:
            await publish(
                ManagerUnavailableEvent(
                    vertical=key,
                    reason="manager_user_not_found",
                    assignment_mode=mode.value,
                )
            )
            return None

        latency_ms = (time.monotonic() - started) * 1000.0
        _record_latency_ms(latency_ms)

        await publish(
            ManagerAssignedEvent(
                pool_manager_id=updated.id,
                manager_id=result.get("user_id"),
                manager_telegram_id=int(result["telegram_id"]),
                manager_name=str(result.get("display_name") or updated.name),
                vertical=key,
                assignment_mode=mode.value,
                request_id=request_id,
                request_number=request_number,
            )
        )
        return result

    @staticmethod
    async def release_manager(
        *,
        pool_manager_id: str | None = None,
        telegram_id: int | None = None,
        vertical: str | None = None,
        request_id: str | None = None,
        request_number: str | None = None,
    ) -> ManagerPoolSnapshot | None:
        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            entry: ManagerPoolSnapshot | None = None
            if pool_manager_id:
                entry = await pool_repo.get_manager_by_id(pool_manager_id)
            elif telegram_id is not None and vertical:
                key = normalize_vertical(vertical) or vertical.strip().lower()
                entry = await pool_repo.get_by_telegram_and_vertical(telegram_id, key)

            if entry is None:
                return None

            previous_load = entry.current_load
            updated = await pool_repo.update_load(entry.id, delta=-1)
            if updated is None:
                return None

            await publish(
                ManagerReleasedEvent(
                    pool_manager_id=updated.id,
                    manager_telegram_id=updated.telegram_id,
                    manager_name=updated.name,
                    vertical=updated.vertical,
                    request_id=request_id,
                    request_number=request_number,
                    previous_load=previous_load,
                    new_load=updated.current_load,
                )
            )
            return updated

    @staticmethod
    async def release_by_manager_uuid(
        manager_uuid: uuid.UUID | str,
        *,
        vertical: str | None = None,
        request_id: str | None = None,
        request_number: str | None = None,
    ) -> ManagerPoolSnapshot | None:
        async with get_session() as session:
            user = await UserRepository(session).get_by_id(uuid.UUID(str(manager_uuid)))
            if user is None or user.telegram_id is None:
                return None
        key = normalize_vertical(vertical) if vertical else None
        if key:
            return await ManagerPoolService.release_manager(
                telegram_id=int(user.telegram_id),
                vertical=key,
                request_id=request_id,
                request_number=request_number,
            )
        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            for entry in await pool_repo.list_all():
                if entry.telegram_id == user.telegram_id:
                    return await ManagerPoolService.release_manager(
                        pool_manager_id=entry.id,
                        request_id=request_id,
                        request_number=request_number,
                    )
        return None

    @staticmethod
    async def calculate_load(*, vertical: str | None = None) -> dict[str, int]:
        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            entries = await pool_repo.list_all(vertical=vertical)
            loads: dict[uuid.UUID, int] = {}
            for entry in entries:
                loads[uuid.UUID(entry.id)] = await pool_repo.count_active_for_telegram(
                    entry.telegram_id
                )
            if loads:
                await pool_repo.set_loads_bulk(loads)
        return {str(k): v for k, v in loads.items()}

    @staticmethod
    async def rebalance(*, vertical: str | None = None) -> dict[str, Any]:
        loads = await ManagerPoolService.calculate_load(vertical=vertical)
        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            entries = await pool_repo.list_all(vertical=vertical)
        active = [e for e in entries if e.is_active]
        total_load = sum(loads.get(e.id, e.current_load) for e in active)
        capacity = max(len(active), 1)
        return {
            "vertical": vertical,
            "assignment_mode": _assignment_mode().value,
            "managers_rebalanced": len(loads),
            "total_load": total_load,
            "average_load": round(total_load / capacity, 2),
            "loads": loads,
        }

    @staticmethod
    async def get_pool_dashboard(*, vertical: str | None = None) -> dict[str, Any]:
        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            entries = await pool_repo.list_all(vertical=vertical)
            active_entries = [e for e in entries if e.is_active]
            telegram_ids = [e.telegram_id for e in active_entries]
            active_requests = await pool_repo.count_active_requests()
            avg_response = await pool_repo.average_response_seconds_for_pool(telegram_ids)

        loads = [e.current_load for e in active_entries]
        total_load = sum(loads)
        capacity = max(len(active_entries), 1)
        busy = sum(1 for load in loads if load > 0)
        idle = len(active_entries) - busy
        avg_latency = (
            round(sum(_assignment_latencies_ms) / len(_assignment_latencies_ms), 2)
            if _assignment_latencies_ms
            else 0.0
        )

        manager_current_load = {e.name: e.current_load for e in active_entries}

        return {
            "assignment_mode": _assignment_mode().value,
            "managers": [e.to_dict() for e in active_entries],
            "active_requests": active_requests,
            "average_response_time_seconds": avg_response,
            "kpi": {
                "manager_current_load": manager_current_load,
                "manager_average_load": round(total_load / capacity, 2),
                "assignment_latency_ms": avg_latency,
                "pool_utilization": round(busy / capacity, 4) if active_entries else 0.0,
                "busy_managers": busy,
                "idle_managers": idle,
            },
        }

    @staticmethod
    async def handle_request_completed(event) -> None:
        from events.request_events import ManagerReassignedEvent, RequestCompletedEvent

        if isinstance(event, RequestCompletedEvent):
            if not event.manager_id:
                return
            await ManagerPoolService.release_by_manager_uuid(
                event.manager_id,
                vertical=event.vertical,
                request_id=event.request_id,
                request_number=event.request_number,
            )
        elif isinstance(event, ManagerReassignedEvent):
            if event.previous_manager_id:
                await ManagerPoolService.release_by_manager_uuid(
                    event.previous_manager_id,
                    vertical=event.vertical,
                    request_id=event.request_id,
                    request_number=event.request_number,
                )

    @staticmethod
    def subscribe_to_event_bus() -> None:
        from events.event_bus import subscribe
        from events.request_events import ManagerReassignedEvent, RequestCompletedEvent

        subscribe(
            RequestCompletedEvent,
            ManagerPoolService.handle_request_completed,
            handler_id="manager_pool_release_completed",
        )
        subscribe(
            ManagerReassignedEvent,
            ManagerPoolService.handle_request_completed,
            handler_id="manager_pool_release_reassigned",
        )

    @staticmethod
    def reset_subscription() -> None:
        pass


manager_pool_service = ManagerPoolService()
