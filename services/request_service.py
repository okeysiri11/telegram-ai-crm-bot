# RequestService — unified request creation for all verticals (PostgreSQL only).

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from database.models.client_request import ClientRequestStatus, CrmFunnelStage
from database.session import get_session
from repositories.request_repository import RequestRepository
from services.manager_service import manager_service
from services.system_roles import Vertical, normalize_vertical

logger = logging.getLogger(__name__)

SUPPORTED_VERTICALS = frozenset({
    Vertical.AUTO.value,
    Vertical.AGRO.value,
    Vertical.REALTY.value,
    Vertical.LEGAL.value,
    Vertical.LOGISTICS.value,
})

VERTICAL_PREFIX = {
    Vertical.AUTO.value: "AUTO",
    Vertical.AGRO.value: "AGRO",
    Vertical.REALTY.value: "REALTY",
    Vertical.LEGAL.value: "LEGAL",
    Vertical.LOGISTICS.value: "LOGISTICS",
}


class RequestService:
    @staticmethod
    async def create_request(
        *,
        vertical: str,
        client_telegram_id: int,
        client_name: str = "",
        client_username: str | None = None,
        product: str = "",
        description: str = "",
        request_type: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        key = normalize_vertical(vertical) or vertical.strip().lower()
        if key not in SUPPORTED_VERTICALS:
            raise ValueError(f"Unsupported vertical: {vertical}")

        if key == Vertical.AUTO.value:
            return await RequestService._create_auto_request(
                client_telegram_id=client_telegram_id,
                client_username=client_username,
                client_full_name=client_name,
                flow_request_type=request_type or extra.get("flow_request_type") or "buy_car",
                description=description or product,
                **extra,
            )

        manager = await manager_service.resolve_manager_for_vertical(key)
        manager_uuid = uuid.UUID(manager["user_id"]) if manager else None

        async with get_session() as session:
            repo = RequestRepository(session)
            prefix = VERTICAL_PREFIX.get(key, key.upper())
            request_number = await repo.next_crm_number(prefix=prefix)
            db_type = request_type or f"{key.upper()}_REQUEST"
            row = await repo.create_crm(
                request_number=request_number,
                request_type=db_type,
                status=ClientRequestStatus.NEW.value,
                funnel_stage=CrmFunnelStage.NEW_LEAD.value,
                client_telegram_id=client_telegram_id,
                client_username=client_username,
                client_first_name=client_name or None,
                description=description or product or None,
                manager_id=manager_uuid,
                **{k: v for k, v in extra.items() if k not in {"flow_request_type"}},
            )

        result = RequestService._crm_snapshot(row)
        await RequestService._publish_request_created(key, result, manager)
        return result

    @staticmethod
    async def _create_auto_request(**kwargs: Any) -> dict[str, Any]:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await AutoClientRequestEngineV1.submit(**kwargs)

    @staticmethod
    async def _publish_request_created(
        vertical: str,
        request: dict[str, Any],
        manager: dict[str, Any] | None,
    ) -> None:
        from events.event_bus import publish
        from events.request_events import RequestCreatedEvent

        await publish(
            RequestCreatedEvent(
                request_id=str(request.get("id")),
                request_number=str(request.get("request_number")),
                vertical=vertical,
                request_type=str(request.get("request_type") or f"{vertical.upper()}_REQUEST"),
                status=str(request.get("status") or "NEW"),
                client_telegram_id=request.get("client_telegram_id"),
                client_name=str(request.get("client_name") or ""),
                description=str(request.get("description") or ""),
                manager_id=request.get("manager_id"),
                manager_telegram_id=int(manager["telegram_id"]) if manager and manager.get("telegram_id") else None,
            )
        )

    @staticmethod
    async def _publish_request_assigned(result: dict[str, Any], manager_id: uuid.UUID | str) -> None:
        from events.event_bus import publish
        from events.request_events import RequestAssignedEvent

        await publish(
            RequestAssignedEvent(
                request_id=str(result.get("id")),
                request_number=str(result.get("request_number")),
                vertical=str(result.get("vertical") or "unknown"),
                request_type=str(result.get("request_type") or ""),
                manager_id=str(manager_id),
                manager_telegram_id=result.get("manager_telegram_id"),
                client_telegram_id=result.get("client_telegram_id"),
                status=str(result.get("status") or "ASSIGNED"),
            )
        )

    @staticmethod
    async def _publish_manager_first_response(
        result: dict[str, Any],
        manager_id: uuid.UUID | str,
        *,
        response_time_seconds: int = 0,
        sla_compliant: bool = True,
    ) -> None:
        from events.event_bus import publish
        from events.request_events import ManagerFirstResponseEvent

        await publish(
            ManagerFirstResponseEvent(
                request_id=str(result.get("id")),
                request_number=str(result.get("request_number")),
                vertical=str(result.get("vertical") or "unknown"),
                request_type=str(result.get("request_type") or ""),
                manager_id=str(manager_id),
                manager_telegram_id=result.get("manager_telegram_id"),
                client_telegram_id=result.get("client_telegram_id"),
                response_time_seconds=response_time_seconds,
                sla_compliant=sla_compliant,
            )
        )

    @staticmethod
    def _response_seconds_from_snapshot(result: dict[str, Any]) -> int:
        created_raw = result.get("created_at")
        if not created_raw:
            return 0
        try:
            if isinstance(created_raw, datetime):
                created = created_raw if created_raw.tzinfo else created_raw.replace(tzinfo=timezone.utc)
            else:
                created = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
            return max(0, int((datetime.now(timezone.utc) - created).total_seconds()))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    async def _publish_request_completed(result: dict[str, Any], *, converted_to_deal: bool = False) -> None:
        from events.event_bus import publish
        from events.request_events import RequestCompletedEvent

        await publish(
            RequestCompletedEvent(
                request_id=str(result.get("id")),
                request_number=str(result.get("request_number")),
                vertical=str(result.get("vertical") or "unknown"),
                request_type=str(result.get("request_type") or ""),
                status=str(result.get("status") or "COMPLETED"),
                manager_id=result.get("manager_id"),
                client_telegram_id=result.get("client_telegram_id"),
                converted_to_deal=converted_to_deal,
            )
        )

    @staticmethod
    async def _publish_manager_reassigned(
        result: dict[str, Any],
        *,
        manager_id: uuid.UUID | str,
        previous_manager_id: str | None,
        manager_telegram_id: int | None = None,
    ) -> None:
        from events.event_bus import publish
        from events.request_events import ManagerReassignedEvent

        await publish(
            ManagerReassignedEvent(
                request_id=str(result.get("id")),
                request_number=str(result.get("request_number")),
                vertical=str(result.get("vertical") or "unknown"),
                request_type=str(result.get("request_type") or ""),
                previous_manager_id=previous_manager_id,
                manager_id=str(manager_id),
                manager_telegram_id=manager_telegram_id,
                client_telegram_id=result.get("client_telegram_id"),
            )
        )

    @staticmethod
    async def publish_request_overdue(
        *,
        request_id: str,
        request_number: str,
        vertical: str,
        request_type: str,
        manager_id: str | None = None,
        manager_telegram_id: int | None = None,
        overdue_seconds: int = 0,
        reason: str = "sla_first_response",
    ) -> None:
        from events.event_bus import publish
        from events.request_events import RequestOverdueEvent

        await publish(
            RequestOverdueEvent(
                request_id=request_id,
                request_number=request_number,
                vertical=vertical,
                request_type=request_type,
                manager_id=manager_id,
                manager_telegram_id=manager_telegram_id,
                overdue_seconds=overdue_seconds,
                reason=reason,
            )
        )

    @staticmethod
    async def get_request(request_number: str) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = RequestRepository(session)
            auto = await repo.get_auto_by_number(request_number)
            if auto is not None:
                return RequestService._auto_snapshot(auto)
            crm = await repo.get_crm_by_number(request_number)
            if crm is not None:
                return RequestService._crm_snapshot(crm)
        return None

    @staticmethod
    async def change_status(
        *,
        request_number: str,
        new_status: str,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any] | None:
        from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

        if request_number.startswith("AUTO-"):
            from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

            summary = await AutoClientRequestEngineV1.get_request_summary(request_number)
            if summary is None:
                return None
            # Status updates for auto requests go through CRM engine when linked.
            return summary

        return await ClientRequestCrmEngineV1.update_status(
            request_number,
            new_status,
            actor_telegram_id=actor_telegram_id,
        )

    @staticmethod
    async def assign_manager(
        *,
        request_number: str,
        manager_telegram_id: int | None = None,
        vertical: str | None = None,
    ) -> dict[str, Any] | None:
        from repositories.user_repository import UserRepository

        if manager_telegram_id is None and vertical:
            mgr = await manager_service.resolve_manager_for_vertical(vertical)
            if mgr is None:
                return None
            manager_telegram_id = int(mgr["telegram_id"])

        if manager_telegram_id is None:
            return None

        async with get_session() as session:
            user = await UserRepository(session).get_by_telegram_id(manager_telegram_id)
            if user is None:
                return None
            repo = RequestRepository(session)
            crm = await repo.get_crm_by_number(request_number)
            if crm is None:
                return None
            row = await repo.update_crm(crm, manager_id=user.id, status=ClientRequestStatus.ASSIGNED.value)
            return RequestService._crm_snapshot(row)

    @staticmethod
    def _crm_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "request_number": row.request_number,
            "request_type": row.request_type,
            "status": row.status,
            "vertical": (row.request_type or "").split("_")[0].lower(),
            "client_telegram_id": row.client_telegram_id,
            "client_name": row.client_first_name or row.client_username,
            "description": row.description,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    def _auto_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "request_number": row.request_number,
            "request_type": row.request_type,
            "status": row.status,
            "vertical": Vertical.AUTO.value,
            "client_telegram_id": row.client_telegram_id,
            "client_name": row.client_full_name or row.client_username,
            "description": row.description,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    def _merge_request_snapshots(crm_rows, auto_rows, *, limit: int = 20) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for row in crm_rows:
            merged.append(RequestService._crm_snapshot(row))
        for row in auto_rows:
            snap = RequestService._auto_snapshot(row)
            if not any(item["request_number"] == snap["request_number"] for item in merged):
                merged.append(snap)
        merged.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return merged[:limit]

    @staticmethod
    async def _resolve_request_number(request_id: str) -> str | None:
        raw = str(request_id).strip()
        try:
            rid = uuid.UUID(raw)
        except ValueError:
            existing = await RequestService.get_request(raw)
            return existing.get("request_number") if existing else None

        async with get_session() as session:
            repo = RequestRepository(session)
            crm = await repo.get_crm_by_id(rid)
            if crm is not None:
                return crm.request_number
            auto = await repo.get_auto_by_id(rid)
            if auto is not None:
                return auto.request_number
        return None

    @staticmethod
    async def get_new_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        mid = uuid.UUID(str(manager_id))
        async with get_session() as session:
            crm_rows, auto_rows = await RequestRepository(session).list_new_for_manager(mid, limit=limit)
        return RequestService._merge_request_snapshots(crm_rows, auto_rows, limit=limit)

    @staticmethod
    async def get_active_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        mid = uuid.UUID(str(manager_id))
        async with get_session() as session:
            crm_rows, auto_rows = await RequestRepository(session).list_active_for_manager(mid, limit=limit)
        return RequestService._merge_request_snapshots(crm_rows, auto_rows, limit=limit)

    @staticmethod
    async def get_completed_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        mid = uuid.UUID(str(manager_id))
        async with get_session() as session:
            crm_rows, auto_rows = await RequestRepository(session).list_completed_for_manager(mid, limit=limit)
        return RequestService._merge_request_snapshots(crm_rows, auto_rows, limit=limit)

    @staticmethod
    async def get_overdue_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        from datetime import datetime, timedelta, timezone

        from config import SLA_FIRST_RESPONSE_SEC

        mid = uuid.UUID(str(manager_id))
        before = datetime.now(timezone.utc) - timedelta(seconds=SLA_FIRST_RESPONSE_SEC)
        async with get_session() as session:
            crm_rows, auto_rows = await RequestRepository(session).list_overdue_for_manager(
                mid,
                before=before,
                limit=limit,
            )
        return RequestService._merge_request_snapshots(crm_rows, auto_rows, limit=limit)

    @staticmethod
    async def _assign_request_to_manager(
        request_id: str,
        manager_id: uuid.UUID | str,
    ) -> dict[str, Any] | None:
        from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

        request_number = await RequestService._resolve_request_number(request_id)
        if request_number is None:
            return None

        mid = uuid.UUID(str(manager_id))
        result = await ClientRequestCrmEngineV1.assign_manager(request_number, mid)
        if result is not None:
            return {
                "id": result.get("id"),
                "request_number": result.get("request_number"),
                "request_type": result.get("request_type"),
                "status": result.get("status"),
                "vertical": (result.get("request_type") or "").split("_")[0].lower(),
                "client_telegram_id": result.get("client_telegram_id"),
                "client_name": result.get("client_username"),
                "description": result.get("description"),
                "manager_id": str(mid),
            }

        async with get_session() as session:
            repo = RequestRepository(session)
            auto = await repo.get_auto_by_number(request_number)
            if auto is None:
                return None
            row = await repo._auto().update(
                auto,
                manager_id=mid,
                status=ClientRequestStatus.ASSIGNED.value,
            )
            return RequestService._auto_snapshot(row)

    @staticmethod
    async def take_request(
        request_id: str,
        manager_id: uuid.UUID | str,
    ) -> dict[str, Any] | None:
        result = await RequestService._assign_request_to_manager(request_id, manager_id)
        if result is not None:
            await RequestService._publish_request_assigned(result, manager_id)
            response_secs = RequestService._response_seconds_from_snapshot(result)
            await RequestService._publish_manager_first_response(
                result,
                manager_id,
                response_time_seconds=response_secs,
            )
        return result

    @staticmethod
    async def complete_request(request_id: str) -> dict[str, Any] | None:
        from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

        request_number = await RequestService._resolve_request_number(request_id)
        if request_number is None:
            return None

        try:
            result = await ClientRequestCrmEngineV1.update_status(
                request_number,
                ClientRequestStatus.COMPLETED.value,
            )
        except ValueError:
            result = None

        if result is not None:
            await RequestService._publish_request_completed(result)
            return result

        async with get_session() as session:
            repo = RequestRepository(session)
            auto = await repo.get_auto_by_number(request_number)
            if auto is None:
                return None
            row = await repo._auto().update(auto, status="DONE")
            snapshot = RequestService._auto_snapshot(row)
            await RequestService._publish_request_completed(snapshot)
            return snapshot

    @staticmethod
    async def reassign_request(
        request_id: str,
        manager_id: uuid.UUID | str,
    ) -> dict[str, Any] | None:
        existing = await RequestService.get_request(str(request_id))
        if existing is None:
            resolved = await RequestService._resolve_request_number(str(request_id))
            if resolved:
                existing = await RequestService.get_request(resolved)
        previous_manager_id = existing.get("manager_id") if existing else None

        result = await RequestService._assign_request_to_manager(request_id, manager_id)
        if result is None:
            return None

        await RequestService._publish_manager_reassigned(
            result,
            manager_id=manager_id,
            previous_manager_id=previous_manager_id,
        )
        return result


request_service = RequestService()
