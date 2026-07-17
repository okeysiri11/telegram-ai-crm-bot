# Client Request CRM engine — pipeline, funnel, history, status updates.

from __future__ import annotations

import logging
import uuid
from typing import Any

from database.models.client_request import (
    ClientRequestStatus,
    CrmFunnelStage,
)
from database.session import get_session
from repositories.client_request_repository import ClientRequestRepository

logger = logging.getLogger(__name__)

STATUS_LABELS: dict[str, str] = {
    ClientRequestStatus.NEW.value: "🆕 Новая",
    ClientRequestStatus.ASSIGNED.value: "👤 Назначена",
    ClientRequestStatus.IN_PROGRESS.value: "🟡 В работе",
    ClientRequestStatus.WAITING_CLIENT.value: "⏳ Ожидает клиента",
    ClientRequestStatus.COMPLETED.value: "✅ Завершена",
    ClientRequestStatus.CANCELLED.value: "❌ Отменена",
}

FUNNEL_LABELS: dict[str, str] = {
    CrmFunnelStage.NEW_LEAD.value: "Новый лид",
    CrmFunnelStage.CONTACTED.value: "Контакт",
    CrmFunnelStage.NEGOTIATION.value: "Переговоры",
    CrmFunnelStage.PROPOSAL.value: "Предложение",
    CrmFunnelStage.DEAL.value: "Сделка",
    CrmFunnelStage.CLOSED.value: "Закрыта",
    CrmFunnelStage.LOST.value: "Потеряна",
}

REQUEST_TYPE_DISPLAY: dict[str, str] = {
    "buy_car": "🚗 Поиск автомобиля",
    "sell_car": "💰 Продажа автомобиля",
    "listing": "📢 Размещение объявления",
    "services": "🛠 Автоуслуги",
    "manager_callback": "📞 Связь с менеджером",
    "AUTO_SEARCH": "🚗 Поиск автомобиля",
    "AUTO_SELL": "💰 Продажа автомобиля",
    "AUTO_LISTING": "📢 Размещение объявления",
    "AUTO_SERVICES": "🛠 Автоуслуги",
    "AUTO_MANAGER_CALLBACK": "📞 Связь с менеджером",
}

FUNNEL_TRANSITIONS: dict[str, frozenset[str]] = {
    CrmFunnelStage.NEW_LEAD.value: frozenset({CrmFunnelStage.CONTACTED.value, CrmFunnelStage.LOST.value}),
    CrmFunnelStage.CONTACTED.value: frozenset({CrmFunnelStage.NEGOTIATION.value, CrmFunnelStage.LOST.value}),
    CrmFunnelStage.NEGOTIATION.value: frozenset({CrmFunnelStage.PROPOSAL.value, CrmFunnelStage.LOST.value}),
    CrmFunnelStage.PROPOSAL.value: frozenset({CrmFunnelStage.DEAL.value, CrmFunnelStage.LOST.value}),
    CrmFunnelStage.DEAL.value: frozenset({CrmFunnelStage.CLOSED.value, CrmFunnelStage.LOST.value}),
    CrmFunnelStage.CLOSED.value: frozenset(),
    CrmFunnelStage.LOST.value: frozenset(),
}

STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    ClientRequestStatus.NEW.value: frozenset({
        ClientRequestStatus.ASSIGNED.value,
        ClientRequestStatus.IN_PROGRESS.value,
        ClientRequestStatus.CANCELLED.value,
    }),
    ClientRequestStatus.ASSIGNED.value: frozenset({
        ClientRequestStatus.IN_PROGRESS.value,
        ClientRequestStatus.CANCELLED.value,
    }),
    ClientRequestStatus.IN_PROGRESS.value: frozenset({
        ClientRequestStatus.WAITING_CLIENT.value,
        ClientRequestStatus.COMPLETED.value,
        ClientRequestStatus.CANCELLED.value,
    }),
    ClientRequestStatus.WAITING_CLIENT.value: frozenset({
        ClientRequestStatus.IN_PROGRESS.value,
        ClientRequestStatus.COMPLETED.value,
        ClientRequestStatus.CANCELLED.value,
    }),
    ClientRequestStatus.COMPLETED.value: frozenset(),
    ClientRequestStatus.CANCELLED.value: frozenset(),
}


class ClientRequestCrmEngineV1:
    @staticmethod
    def status_label(status: str) -> str:
        return STATUS_LABELS.get(status, status)

    @staticmethod
    def request_type_label(request_type: str) -> str:
        return REQUEST_TYPE_DISPLAY.get(request_type, request_type)

    @staticmethod
    async def sync_from_auto_request(
        *,
        auto_request_id: uuid.UUID,
        request_number: str,
        flow_request_type: str,
        manager_id: uuid.UUID | None,
        client_telegram_id: int,
        client_username: str | None = None,
        client_first_name: str | None = None,
        client_last_name: str | None = None,
        client_phone: str | None = None,
        client_language_code: str | None = None,
        description: str | None = None,
        photo_file_ids: list[str] | None = None,
        vin: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year: int | None = None,
        mileage: int | None = None,
        budget: float | None = None,
        price: float | None = None,
        fuel: str | None = None,
        engine: str | None = None,
        transmission: str | None = None,
        city: str | None = None,
        service_type: str | None = None,
        ai_qualification: dict | None = None,
    ) -> dict[str, Any]:
        from services.pg_auto_client_request_engine import FLOW_TYPE_TO_DB

        db_type = FLOW_TYPE_TO_DB.get(flow_request_type, flow_request_type)

        async with get_session() as session:
            repo = ClientRequestRepository(session)
            existing = await repo.get_by_number(request_number)
            if existing:
                row = await repo.update(
                    existing,
                    auto_request_id=auto_request_id,
                    photo_file_ids=photo_file_ids or existing.photo_file_ids,
                )
            else:
                row = await repo.create(
                    request_number=request_number,
                    request_type=db_type,
                    status=ClientRequestStatus.ASSIGNED.value if manager_id else ClientRequestStatus.NEW.value,
                    funnel_stage=CrmFunnelStage.NEW_LEAD.value,
                    client_telegram_id=client_telegram_id,
                    client_username=client_username,
                    client_first_name=client_first_name,
                    client_last_name=client_last_name,
                    client_phone=client_phone,
                    client_language_code=client_language_code,
                    description=description,
                    photo_file_ids=photo_file_ids,
                    vin=vin,
                    brand=brand,
                    model=model,
                    year=year,
                    mileage=mileage,
                    budget=budget,
                    price=price,
                    fuel=fuel,
                    engine=engine,
                    transmission=transmission,
                    city=city,
                    service_type=service_type,
                    ai_qualification=ai_qualification,
                    manager_id=manager_id,
                    auto_request_id=auto_request_id,
                )

            from sqlalchemy import update
            from database.models.auto_client_request import AutoClientRequest

            await session.execute(
                update(AutoClientRequest)
                .where(AutoClientRequest.id == auto_request_id)
                .values(client_request_id=row.id, funnel_stage=CrmFunnelStage.NEW_LEAD.value)
            )

            request_id = row.id
            request_status = row.status

        await ClientRequestCrmEngineV1._publish_event(
            "client_request.created",
            request_id,
            {
                "request_number": request_number,
                "request_type": db_type,
                "status": request_status,
                "vertical": "auto",
                "manager_id": str(manager_id) if manager_id else None,
                "client_telegram_id": client_telegram_id,
            },
        )
        try:
            from services.pg_platform_audit_engine import PlatformAuditEngineV1
            from services.pg_lead_sla_engine import LeadSlaEngineV1

            await PlatformAuditEngineV1.lead_created(
                str(request_id),
                user_id=client_telegram_id,
                request_number=request_number,
                request_type=db_type,
            )
            await LeadSlaEngineV1.on_lead_created(
                client_request_id=request_id,
                request_number=request_number,
            )
            if manager_id:
                await LeadSlaEngineV1.on_assigned(request_number=request_number)
                await PlatformAuditEngineV1.manager_assigned(
                    str(request_id),
                    request_number=request_number,
                    manager_id=str(manager_id),
                )
        except Exception:
            logger.warning("Post-create audit/SLA hook failed", exc_info=True)

        logger.info("CLIENT_REQUEST synced id=%s number=%s", request_id, request_number)
        return {"id": str(request_id), "request_number": request_number}

    @staticmethod
    async def list_client_history(client_telegram_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await ClientRequestRepository(session).list_for_client(
                client_telegram_id,
                limit=limit,
            )
        return [ClientRequestCrmEngineV1._snapshot(r) for r in rows]

    @staticmethod
    async def get_request_detail(request_number: str) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await ClientRequestRepository(session).get_by_number(request_number)
        return ClientRequestCrmEngineV1._snapshot(row) if row else None

    @staticmethod
    async def list_manager_leads(
        manager_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await ClientRequestRepository(session).list_for_manager(
                manager_id,
                status=status,
                limit=limit,
            )
        return [ClientRequestCrmEngineV1._snapshot(r) for r in rows]

    @staticmethod
    async def list_new_leads(*, limit: int = 20) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await ClientRequestRepository(session).list_new(limit=limit)
        return [ClientRequestCrmEngineV1._snapshot(r) for r in rows]

    @staticmethod
    async def update_status(
        request_number: str,
        new_status: str,
        *,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any] | None:
        if new_status not in STATUS_LABELS:
            raise ValueError(f"Unknown status: {new_status}")

        async with get_session() as session:
            repo = ClientRequestRepository(session)
            row = await repo.get_by_number(request_number)
            if row is None:
                return None

            allowed = STATUS_TRANSITIONS.get(row.status, frozenset())
            if new_status != row.status and new_status not in allowed:
                raise ValueError(f"Transition {row.status} -> {new_status} not allowed")

            row = await repo.update(row, status=new_status)

            from sqlalchemy import update
            from database.models.auto_client_request import AutoClientRequest

            auto_status = new_status if new_status != ClientRequestStatus.COMPLETED.value else "DONE"
            await session.execute(
                update(AutoClientRequest)
                .where(AutoClientRequest.request_number == request_number)
                .values(status=auto_status)
            )
            snapshot = ClientRequestCrmEngineV1._snapshot(row)
            client_telegram_id = row.client_telegram_id
            request_id = row.id
            funnel_stage = row.funnel_stage
            manager_id = row.manager_id

        await ClientRequestCrmEngineV1._publish_event(
            "client_request.status_changed",
            request_id,
            {
                "request_number": request_number,
                "status": new_status,
                "actor": actor_telegram_id,
                "funnel_stage": funnel_stage,
                "manager_id": str(manager_id) if manager_id else None,
            },
        )
        try:
            from services.pg_platform_audit_engine import PlatformAuditEngineV1
            from services.pg_lead_sla_engine import LeadSlaEngineV1

            await PlatformAuditEngineV1.status_changed(
                str(request_id),
                user_id=actor_telegram_id,
                request_number=request_number,
                status=new_status,
            )
            if new_status == ClientRequestStatus.IN_PROGRESS.value:
                await LeadSlaEngineV1.on_first_response(request_number)
            if new_status in {
                ClientRequestStatus.COMPLETED.value,
                ClientRequestStatus.CANCELLED.value,
            }:
                await LeadSlaEngineV1.on_closed(request_number)
        except Exception:
            logger.warning("Status audit/SLA hook failed", exc_info=True)

        await ClientRequestCrmEngineV1._notify_client_status(client_telegram_id, request_number, new_status)
        return snapshot

    @staticmethod
    async def update_funnel_stage(request_number: str, new_stage: str) -> dict[str, Any] | None:
        if new_stage not in FUNNEL_LABELS:
            raise ValueError(f"Unknown funnel stage: {new_stage}")

        async with get_session() as session:
            repo = ClientRequestRepository(session)
            row = await repo.get_by_number(request_number)
            if row is None:
                return None

            allowed = FUNNEL_TRANSITIONS.get(row.funnel_stage, frozenset())
            if new_stage != row.funnel_stage and new_stage not in allowed:
                raise ValueError(f"Funnel transition {row.funnel_stage} -> {new_stage} not allowed")

            row = await repo.update(row, funnel_stage=new_stage)

            from sqlalchemy import update
            from database.models.auto_client_request import AutoClientRequest

            await session.execute(
                update(AutoClientRequest)
                .where(AutoClientRequest.request_number == request_number)
                .values(funnel_stage=new_stage)
            )
            request_id = row.id

        await ClientRequestCrmEngineV1._publish_event(
            "client_request.funnel_changed",
            request_id,
            {"request_number": request_number, "funnel_stage": new_stage},
        )
        return ClientRequestCrmEngineV1._snapshot(row)

    @staticmethod
    async def assign_manager(request_number: str, manager_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = ClientRequestRepository(session)
            row = await repo.get_by_number(request_number)
            if row is None:
                return None
            row = await repo.update(
                row,
                manager_id=manager_id,
                status=ClientRequestStatus.ASSIGNED.value,
            )

            from sqlalchemy import update
            from database.models.auto_client_request import AutoClientRequest

            await session.execute(
                update(AutoClientRequest)
                .where(AutoClientRequest.request_number == request_number)
                .values(manager_id=manager_id, status=ClientRequestStatus.ASSIGNED.value)
            )
            snapshot = ClientRequestCrmEngineV1._snapshot(row)
            request_id = row.id

        await ClientRequestCrmEngineV1._publish_event(
            "client_request.assigned",
            request_id,
            {"request_number": request_number, "manager_id": str(manager_id)},
        )
        return snapshot

    @staticmethod
    def _snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "request_number": row.request_number,
            "request_type": row.request_type,
            "request_type_label": ClientRequestCrmEngineV1.request_type_label(row.request_type),
            "status": row.status,
            "status_label": ClientRequestCrmEngineV1.status_label(row.status),
            "funnel_stage": row.funnel_stage,
            "funnel_label": FUNNEL_LABELS.get(row.funnel_stage, row.funnel_stage),
            "client_telegram_id": row.client_telegram_id,
            "client_username": row.client_username,
            "client_phone": row.client_phone,
            "description": row.description,
            "brand": row.brand,
            "model": row.model,
            "year": row.year,
            "price": float(row.price) if row.price is not None else None,
            "photo_count": len(row.photo_file_ids or []),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    async def _notify_client_status(
        client_telegram_id: int,
        request_number: str,
        status: str,
    ) -> None:
        from config import BOT_TOKEN
        from aiogram import Bot

        if not BOT_TOKEN:
            return
        label = ClientRequestCrmEngineV1.status_label(status)
        text = (
            f"Статус вашей заявки изменён:\n\n"
            f"📋 {request_number}\n"
            f"{label}"
        )
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(chat_id=client_telegram_id, text=text)
        except Exception:
            logger.warning("Failed to notify client %s about status", client_telegram_id, exc_info=True)
        finally:
            await bot.session.close()

    @staticmethod
    async def _publish_event(event_type: str, aggregate_id: uuid.UUID, payload: dict) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type=event_type,
                aggregate_type="client_request",
                aggregate_id=aggregate_id,
                payload=payload,
            )
        except Exception:
            logger.warning("Event bus publish failed type=%s", event_type, exc_info=True)
