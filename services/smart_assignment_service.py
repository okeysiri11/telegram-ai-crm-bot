# SmartAssignmentService — intelligent manager selection with learning dataset.

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from database.session import get_session
from events.event_bus import publish
from events.manager_pool_events import ManagerAssignedEvent, ManagerUnavailableEvent
from events.smart_assignment_events import (
    SmartAssignmentCalculatedEvent,
    SmartAssignmentCompletedEvent,
)
from models.assignment_score import (
    AssignmentSegment,
    AssignmentStrategy,
    ManagerCandidateMetrics,
    ManagerCandidateScore,
    ScoreWeights,
    segment_from_request_type,
    segment_from_vertical,
)
from models.manager_pool import AssignmentMode, ManagerPoolSnapshot
from repositories.assignment_score_repository import AssignmentScoreRepository
from repositories.manager_pool_repository import ManagerPoolRepository
from repositories.manager_repository import ManagerRepository
from repositories.user_repository import UserRepository
from platform_configuration.config_provider import config_provider
from services.manager_pool_service import ManagerPoolService
from services.system_roles import normalize_vertical

logger = logging.getLogger(__name__)

_assignment_latencies_ms: list[float] = []
_assignment_failures = 0
_MAX_LATENCY_SAMPLES = 200


def _strategy() -> AssignmentStrategy:
    mode = config_provider.assignment_mode()
    try:
        return AssignmentStrategy(mode)
    except ValueError:
        logger.warning("Invalid assignment mode=%s — using SMART", mode)
        return AssignmentStrategy.SMART


def _record_latency_ms(duration_ms: float) -> None:
    _assignment_latencies_ms.append(duration_ms)
    if len(_assignment_latencies_ms) > _MAX_LATENCY_SAMPLES:
        del _assignment_latencies_ms[0 : len(_assignment_latencies_ms) - _MAX_LATENCY_SAMPLES]


class SmartAssignmentService:
    @staticmethod
    def strategy_name() -> str:
        return _strategy().value

    @staticmethod
    def detect_segment(
        *,
        vertical: str | None = None,
        request_type: str | None = None,
        **_: Any,
    ) -> AssignmentSegment:
        from_type = segment_from_request_type(request_type)
        if from_type is not None:
            return from_type
        return segment_from_vertical(vertical)

    @staticmethod
    def _specialization_matches(segment: AssignmentSegment, specialization: str) -> bool:
        spec = (specialization or "").upper()
        if spec in {"", "MULTI"}:
            return spec == "MULTI"
        return spec == segment.value

    @staticmethod
    def calculate_score(
        candidate: ManagerCandidateMetrics,
        segment: AssignmentSegment,
        *,
        weights: ScoreWeights | None = None,
        max_load: int = 10,
        max_response: float = 3600.0,
        max_completed: int = 100,
        max_priority: int = 200,
    ) -> ManagerCandidateScore:
        w = (weights or ScoreWeights.from_config()).normalized()

        load_norm = 1.0 - min(candidate.current_load / max(max_load, 1), 1.0)
        if candidate.average_response_seconds is None:
            response_norm = 0.5
        else:
            response_norm = 1.0 - min(candidate.average_response_seconds / max(max_response, 1.0), 1.0)
        completed_norm = min(candidate.completed_requests / max(max_completed, 1), 1.0)
        priority_norm = min(candidate.priority / max(max_priority, 1), 1.0)
        specialization_norm = (
            1.0
            if SmartAssignmentService._specialization_matches(segment, candidate.specialization)
            else 0.0
        )

        breakdown = {
            "load": load_norm * w.load,
            "response": response_norm * w.response,
            "completed": completed_norm * w.completed,
            "priority": priority_norm * w.priority,
            "specialization": specialization_norm * w.specialization,
        }
        total = sum(breakdown.values())
        return ManagerCandidateScore(
            candidate=candidate,
            total_score=round(total, 6),
            breakdown=breakdown,
        )

    @staticmethod
    async def _build_candidate_metrics(
        entry: ManagerPoolSnapshot,
        score_repo: AssignmentScoreRepository,
        pool_repo: ManagerPoolRepository,
    ) -> ManagerCandidateMetrics:
        completed = await score_repo.count_completed_for_manager(entry.id)
        avg_response = await score_repo.average_response_from_metrics(entry.telegram_id)
        if avg_response is None:
            avg_response = await score_repo.average_response_for_manager(entry.telegram_id)
        return ManagerCandidateMetrics(
            pool_id=entry.id,
            telegram_id=entry.telegram_id,
            name=entry.name,
            vertical=entry.vertical,
            specialization=entry.specialization,
            priority=entry.priority,
            current_load=entry.current_load,
            average_response_seconds=avg_response,
            completed_requests=completed,
        )

    @staticmethod
    async def get_candidates(
        segment: AssignmentSegment,
        *,
        for_update: bool = False,
    ) -> list[ManagerPoolSnapshot]:
        async with get_session() as session:
            return await ManagerPoolRepository(session).get_available_for_segment(
                segment.value,
                for_update=for_update,
            )

    @staticmethod
    async def score_candidates(
        candidates: list[ManagerPoolSnapshot],
        segment: AssignmentSegment,
    ) -> list[ManagerCandidateScore]:
        if not candidates:
            return []
        async with get_session() as session:
            score_repo = AssignmentScoreRepository(session)
            pool_repo = ManagerPoolRepository(session)
            metrics = [
                await SmartAssignmentService._build_candidate_metrics(entry, score_repo, pool_repo)
                for entry in candidates
            ]
        return [
            SmartAssignmentService.calculate_score(metric, segment)
            for metric in metrics
        ]

    @staticmethod
    def _pick_fallback(
        candidates: list[ManagerPoolSnapshot],
        strategy: AssignmentStrategy,
        *,
        exclude_telegram_ids: set[int] | None = None,
    ) -> ManagerPoolSnapshot | None:
        mode_map = {
            AssignmentStrategy.ROUND_ROBIN: AssignmentMode.ROUND_ROBIN,
            AssignmentStrategy.LEAST_LOADED: AssignmentMode.LEAST_LOADED,
            AssignmentStrategy.PRIORITY: AssignmentMode.PRIORITY,
            AssignmentStrategy.WEIGHTED: AssignmentMode.WEIGHTED,
        }
        mode = mode_map.get(strategy, AssignmentMode.ROUND_ROBIN)
        return ManagerPoolService._select_manager(
            candidates,
            mode,
            exclude_telegram_ids=exclude_telegram_ids,
        )

    @staticmethod
    async def assign_for_request(
        *,
        vertical: str | None = None,
        request_type: str | None = None,
        request_id: str | None = None,
        request_number: str | None = None,
        exclude_telegram_ids: set[int] | None = None,
        increment_load: bool = True,
    ) -> dict[str, Any] | None:
        """Full assignment pipeline: segment → candidates → score → assign → events."""
        started = time.monotonic()
        strategy = _strategy()
        segment = SmartAssignmentService.detect_segment(
            vertical=vertical,
            request_type=request_type,
        )

        async with get_session() as session:
            pool_repo = ManagerPoolRepository(session)
            candidates = await pool_repo.get_available_for_segment(
                segment.value,
                for_update=True,
            )
            if exclude_telegram_ids:
                candidates = [c for c in candidates if c.telegram_id not in exclude_telegram_ids]

            if not candidates:
                global _assignment_failures
                _assignment_failures += 1
                await publish(
                    ManagerUnavailableEvent(
                        vertical=segment.value.lower(),
                        reason="no_active_managers_for_segment",
                        assignment_mode=strategy.value,
                    )
                )
                return None

            selected_score: ManagerCandidateScore | None = None
            scored: list[ManagerCandidateScore] = []

            if strategy == AssignmentStrategy.SMART:
                score_repo = AssignmentScoreRepository(session)
                metrics = [
                    await SmartAssignmentService._build_candidate_metrics(entry, score_repo, pool_repo)
                    for entry in candidates
                ]
                scored = [
                    SmartAssignmentService.calculate_score(metric, segment)
                    for metric in metrics
                ]
                selected_score = max(scored, key=lambda s: s.total_score)
                picked = next(
                    (c for c in candidates if c.id == selected_score.candidate.pool_id),
                    candidates[0],
                )
            else:
                picked = SmartAssignmentService._pick_fallback(
                    candidates,
                    strategy,
                    exclude_telegram_ids=exclude_telegram_ids,
                )
                if picked is None:
                    _assignment_failures += 1
                    await publish(
                        ManagerUnavailableEvent(
                            vertical=segment.value.lower(),
                            reason="no_manager_after_fallback",
                            assignment_mode=strategy.value,
                        )
                    )
                    return None
                selected_score = ManagerCandidateScore(
                    candidate=ManagerCandidateMetrics(
                        pool_id=picked.id,
                        telegram_id=picked.telegram_id,
                        name=picked.name,
                        vertical=picked.vertical,
                        specialization=picked.specialization,
                        priority=picked.priority,
                        current_load=picked.current_load,
                    ),
                    total_score=0.0,
                )

            updated = picked
            if increment_load:
                updated = await pool_repo.update_load(picked.id, delta=1) or picked
            updated = await pool_repo.touch_last_assigned(picked.id) or updated

            user = await UserRepository(session).get_by_telegram_id(updated.telegram_id)
            manager_user_id = str(user.id) if user else None

            score_repo = AssignmentScoreRepository(session)
            record = await score_repo.create_record(
                request_id=request_id,
                request_number=request_number,
                manager_pool_id=updated.id,
                manager_user_id=manager_user_id,
                manager_telegram_id=updated.telegram_id,
                segment=segment.value,
                score=selected_score.total_score if selected_score else 0.0,
                strategy=strategy.value,
                specialization=updated.specialization,
            )

        latency_ms = (time.monotonic() - started) * 1000.0
        _record_latency_ms(latency_ms)

        result = await SmartAssignmentService._manager_snapshot(updated, user)
        if result is None:
            _assignment_failures += 1
            return None

        if strategy == AssignmentStrategy.SMART and scored:
            await publish(
                SmartAssignmentCalculatedEvent(
                    request_id=request_id,
                    request_number=request_number,
                    segment=segment.value,
                    strategy=strategy.value,
                    candidate_count=len(candidates),
                    scores=[s.to_dict() for s in scored],
                    selected_pool_id=updated.id,
                    selected_score=selected_score.total_score if selected_score else 0.0,
                    assignment_latency_ms=latency_ms,
                )
            )

        await publish(
            SmartAssignmentCompletedEvent(
                assignment_id=record.id,
                request_id=request_id,
                request_number=request_number,
                segment=segment.value,
                strategy=strategy.value,
                manager_pool_id=updated.id,
                manager_id=manager_user_id,
                manager_telegram_id=updated.telegram_id,
                manager_name=updated.name,
                score=selected_score.total_score if selected_score else 0.0,
                specialization=updated.specialization,
            )
        )
        await publish(
            ManagerAssignedEvent(
                pool_manager_id=updated.id,
                manager_id=manager_user_id,
                manager_telegram_id=updated.telegram_id,
                manager_name=updated.name,
                vertical=segment.value.lower(),
                assignment_mode=strategy.value,
                request_id=request_id,
                request_number=request_number,
            )
        )

        result["assignment_id"] = record.id
        result["assignment_score"] = selected_score.total_score if selected_score else 0.0
        result["segment"] = segment.value
        return result

    @staticmethod
    async def _manager_snapshot(
        entry: ManagerPoolSnapshot,
        user: Any | None = None,
    ) -> dict[str, Any] | None:
        if user is None:
            async with get_session() as session:
                user = await UserRepository(session).get_by_telegram_id(entry.telegram_id)
        if user is None or user.telegram_id is None:
            return None
        snap = ManagerRepository.manager_snapshot(user)
        snap["pool_id"] = entry.id
        snap["vertical"] = entry.vertical
        snap["pool_load"] = entry.current_load
        snap["specialization"] = entry.specialization
        return snap

    @staticmethod
    async def get_statistics() -> dict[str, Any]:
        async with get_session() as session:
            stats = await AssignmentScoreRepository(session).get_statistics()

        avg_latency = (
            round(sum(_assignment_latencies_ms) / len(_assignment_latencies_ms), 2)
            if _assignment_latencies_ms
            else 0.0
        )
        stats.update(
            {
                "assignment_strategy": _strategy().value,
                "average_assignment_latency_ms": avg_latency,
                "kpi": {
                    "average_assignment_score": stats.get("average_score", 0.0),
                    "smart_assignment_latency": avg_latency,
                    "specialization_accuracy": stats.get("specialization_accuracy", 0.0),
                    "manager_utilization": stats.get("manager_utilization", {}),
                    "segment_distribution": stats.get("segment_distribution", {}),
                    "assignment_failures": _assignment_failures,
                },
            }
        )
        return stats

    @staticmethod
    async def handle_request_completed(event) -> None:
        from events.request_events import ManagerFirstResponseEvent, RequestCompletedEvent

        if isinstance(event, RequestCompletedEvent):
            if not event.request_id:
                return
            async with get_session() as session:
                await AssignmentScoreRepository(session).mark_completed_by_request(
                    event.request_id,
                )
        elif isinstance(event, ManagerFirstResponseEvent):
            if not event.request_id:
                return
            async with get_session() as session:
                record = await AssignmentScoreRepository(session).get_by_request_id(
                    event.request_id
                )
                if record is None:
                    return
                await AssignmentScoreRepository(session).mark_completed(
                    record.id,
                    response_time_seconds=event.response_time_seconds,
                )

    @staticmethod
    async def handle_manager_reassigned(event) -> None:
        from events.request_events import ManagerReassignedEvent
        from services.manager_pool_service import manager_pool_service

        if isinstance(event, ManagerReassignedEvent) and event.previous_manager_id:
            await manager_pool_service.release_by_manager_uuid(
                event.previous_manager_id,
                vertical=event.vertical,
                request_id=event.request_id,
                request_number=event.request_number,
            )

    @staticmethod
    def subscribe_to_event_bus() -> None:
        from events.event_bus import subscribe
        from events.request_events import (
            ManagerFirstResponseEvent,
            ManagerReassignedEvent,
            RequestCompletedEvent,
        )

        subscribe(
            RequestCompletedEvent,
            SmartAssignmentService.handle_request_completed,
            handler_id="smart_assignment_completed",
        )
        subscribe(
            ManagerFirstResponseEvent,
            SmartAssignmentService.handle_request_completed,
            handler_id="smart_assignment_first_response",
        )
        subscribe(
            ManagerReassignedEvent,
            SmartAssignmentService.handle_manager_reassigned,
            handler_id="smart_assignment_reassigned",
        )

    @staticmethod
    def reset_subscription() -> None:
        pass


smart_assignment_service = SmartAssignmentService()
