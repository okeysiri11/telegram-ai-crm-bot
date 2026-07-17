# RequestService — unified request creation for all verticals (PostgreSQL only).

from __future__ import annotations

import logging
import uuid
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
        await RequestService._post_create_hooks(key, result, manager)
        return result

    @staticmethod
    async def _create_auto_request(**kwargs: Any) -> dict[str, Any]:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await AutoClientRequestEngineV1.submit(**kwargs)

    @staticmethod
    async def _post_create_hooks(
        vertical: str,
        request: dict[str, Any],
        manager: dict[str, Any] | None,
    ) -> None:
        from services.notification_service import notification_service

        await notification_service.notify_managers_new_request(
            vertical=vertical,
            request_number=str(request.get("request_number")),
            client_name=request.get("client_name") or "",
            product=request.get("description") or request.get("request_type") or "",
            manager_telegram_id=manager.get("telegram_id") if manager else None,
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
        }


request_service = RequestService()
