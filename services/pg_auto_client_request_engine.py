# Auto Client request engine — create, assign AUTO_MANAGER, notify.

from __future__ import annotations

import logging
import uuid
from typing import Any

from config import DEFAULT_AUTO_MANAGER_ID
from database.models.auto_client_request import (
    AutoClientRequestStatus,
    AutoClientRequestType,
)
from database.models.role import Role
from database.session import get_session
from repositories.auto_client_request_repository import AutoClientRequestRepository
from repositories.user_role_repository import UserRoleRepository
from repositories.users_repository import UsersRepository
from services.pg_auto_dealer_manager_engine import (
    BORIS_FULL_NAME,
    BORIS_USERNAME,
)

logger = logging.getLogger(__name__)

AUTO_MANAGER_ROLE_CODE = "AUTO_MANAGER"

FLOW_TYPE_TO_DB: dict[str, str] = {
    "buy_car": AutoClientRequestType.AUTO_SEARCH.value,
    "sell_car": AutoClientRequestType.AUTO_SELL.value,
    "listing": AutoClientRequestType.AUTO_LISTING.value,
    "manager_callback": AutoClientRequestType.AUTO_MANAGER_CALLBACK.value,
    "services": AutoClientRequestType.AUTO_SERVICES.value,
}

MANAGER_NOTIFICATION_TITLES: dict[str, str] = {
    AutoClientRequestType.AUTO_SEARCH.value: "🚗 Новая заявка на поиск автомобиля",
    AutoClientRequestType.AUTO_SELL.value: "💰 Новая заявка на продажу автомобиля",
    AutoClientRequestType.AUTO_LISTING.value: "📢 Новое объявление от клиента",
    AutoClientRequestType.AUTO_MANAGER_CALLBACK.value: "📞 Клиент запросил менеджера",
    AutoClientRequestType.AUTO_SERVICES.value: "🛠 Новая заявка на автоуслуги",
}


class AutoClientRequestEngineV1:
    @staticmethod
    async def ensure_auto_manager() -> uuid.UUID | None:
        """Provision default auto manager with permission-engine role AUTO_MANAGER."""
        if DEFAULT_AUTO_MANAGER_ID is None:
            logger.warning("DEFAULT_AUTO_MANAGER_ID is not configured — AUTO_MANAGER skipped")
            return None
        try:
            async with get_session() as session:
                users = UsersRepository(session)
                roles = UserRoleRepository(session)

                manager = await users.ensure_user(
                    telegram_id=DEFAULT_AUTO_MANAGER_ID,
                    username=BORIS_USERNAME,
                    full_name=BORIS_FULL_NAME,
                    is_active=True,
                )

                role = await roles.get_role_by_code(AUTO_MANAGER_ROLE_CODE)
                if role is None:
                    role = Role(
                        code=AUTO_MANAGER_ROLE_CODE,
                        name="Auto Manager",
                        description="Automotive operations manager",
                    )
                    session.add(role)
                    await session.flush()

                await roles.assign_role_by_code(manager.id, AUTO_MANAGER_ROLE_CODE)
                logger.info(
                    "AUTO_MANAGER ensured user_id=%s telegram_id=%s",
                    manager.id,
                    DEFAULT_AUTO_MANAGER_ID,
                )
                return manager.id
        except Exception:
            logger.exception("Failed to ensure AUTO_MANAGER")
            return None

    @staticmethod
    async def find_auto_manager() -> tuple[uuid.UUID, int, str] | None:
        """Return (user_uuid, telegram_id, display_name) for AUTO vertical."""
        await AutoClientRequestEngineV1.ensure_auto_manager()

        from services.pg_vertical_routing_engine import VerticalRoutingEngineV1
        from services.system_roles import Vertical

        routed = await VerticalRoutingEngineV1.resolve_manager_for_vertical(Vertical.AUTO.value)
        if routed is not None:
            return routed

        async with get_session() as session:
            manager = await UserRoleRepository(session).find_user_by_role_code(
                AUTO_MANAGER_ROLE_CODE
            )
            if manager is None:
                manager = await UsersRepository(session).get_by_telegram_id(
                    DEFAULT_AUTO_MANAGER_ID
                )
            if manager is None or manager.telegram_id is None:
                logger.error("AUTO_MANAGER NOT FOUND")
                return None

            display = manager.full_name or BORIS_FULL_NAME
            logger.info(f"MANAGER FOUND {manager.id}")
            return manager.id, manager.telegram_id, display

    @staticmethod
    async def _next_request_number(session) -> str:
        repo = AutoClientRequestRepository(session)
        return f"AUTO-{await repo.count_all() + 1:04d}"

    @staticmethod
    async def submit(
        *,
        flow_request_type: str,
        client_telegram_id: int,
        client_username: str | None = None,
        client_full_name: str | None = None,
        client_phone: str | None = None,
        source_link: str | None = "auto_client",
        description: str | None = None,
        user_description: str | None = None,
        photo_file_id: str | None = None,
        photo_file_ids: list[str] | None = None,
        vin: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year: int | None = None,
        mileage: int | None = None,
        budget: float | None = None,
        price: float | None = None,
        service_type: str | None = None,
        client_first_name: str | None = None,
        client_last_name: str | None = None,
        client_language_code: str | None = None,
        fuel: str | None = None,
        city: str | None = None,
        engine: str | None = None,
        ai_qualification: dict | None = None,
    ) -> dict[str, Any]:
        db_type = FLOW_TYPE_TO_DB.get(
            flow_request_type,
            AutoClientRequestType.AUTO_SEARCH.value,
        )

        manager_info = await AutoClientRequestEngineV1.find_auto_manager()
        if manager_info is None:
            raise RuntimeError("AUTO_MANAGER NOT FOUND")

        manager_uuid, manager_telegram_id, manager_name = manager_info

        resolved_photos = list(photo_file_ids or [])
        if not resolved_photos and photo_file_id:
            resolved_photos = [photo_file_id]
        primary_photo = resolved_photos[0] if resolved_photos else photo_file_id

        async with get_session() as session:
            request_number = await AutoClientRequestEngineV1._next_request_number(session)
            row = await AutoClientRequestRepository(session).create(
                request_number=request_number,
                request_type=db_type,
                status=AutoClientRequestStatus.NEW.value,
                client_telegram_id=client_telegram_id,
                client_username=client_username,
                client_full_name=client_full_name,
                client_phone=client_phone,
                source_link=source_link,
                description=description,
                vin=vin,
                brand=brand,
                model=model,
                year=year,
                mileage=mileage,
                budget=budget,
                price=price,
                service_type=service_type,
                photo_file_id=primary_photo,
                photo_file_ids=resolved_photos or None,
                fuel=fuel,
                city=city,
                engine=engine,
                manager_id=manager_uuid,
            )
            request_id = row.id
            created_number = row.request_number

        logger.info(f"REQUEST CREATED {request_id}")
        logger.info(
            "REQUEST_VIN request=%s VIN_PRESENT=%s",
            created_number,
            bool(vin and str(vin).strip()),
        )

        from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

        crm_result = await ClientRequestCrmEngineV1.sync_from_auto_request(
            auto_request_id=request_id,
            request_number=created_number,
            flow_request_type=flow_request_type,
            manager_id=manager_uuid,
            client_telegram_id=client_telegram_id,
            client_username=client_username,
            client_first_name=client_first_name,
            client_last_name=client_last_name,
            client_phone=client_phone,
            client_language_code=client_language_code,
            description=description,
            photo_file_ids=resolved_photos or None,
            vin=vin,
            brand=brand,
            model=model,
            year=year,
            mileage=mileage,
            budget=budget,
            price=price,
            fuel=fuel,
            city=city,
            service_type=service_type,
            ai_qualification=ai_qualification,
        )

        if flow_request_type == "listing" and crm_result.get("id"):
            from services.pg_marketplace_listing_engine import MarketplaceListingEngineV1

            await MarketplaceListingEngineV1.create_from_client_request(
                client_request_id=uuid.UUID(crm_result["id"]),
                seller_telegram_id=client_telegram_id,
                seller_username=client_username,
                data={
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "price": price,
                    "mileage": mileage,
                    "vin": vin,
                    "fuel": fuel,
                    "city": city,
                    "user_description": user_description or description,
                },
                photo_file_ids=resolved_photos or None,
            )

        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        await ManagerDeliveryEngineV1.notify_auto_client_request(
            request_number=created_number,
            request_type=db_type,
            flow_request_type=flow_request_type,
            description=description,
            user_description=user_description,
            client_username=client_username,
            client_full_name=client_full_name,
            client_phone=client_phone,
            client_telegram_id=client_telegram_id,
            photo_file_id=primary_photo,
            photo_file_ids=resolved_photos or None,
            vin=vin,
            brand=brand,
            model=model,
            year=year,
            mileage=mileage,
            budget=budget,
            price=price,
            service_type=service_type,
            lead_id=str(request_id),
        )

        return {
            "id": str(request_id),
            "request_number": created_number,
            "request_type": db_type,
            "manager_id": str(manager_uuid),
            "manager_name": manager_name,
            "manager_telegram_id": manager_telegram_id,
            "client_request_id": crm_result.get("id"),
        }

    @staticmethod
    async def _notify_manager(
        *,
        manager_telegram_id: int,
        request_type: str,
        request_number: str,
        client_username: str | None,
        client_full_name: str | None,
        description: str | None,
        photo_file_id: str | None,
    ) -> None:
        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        await ManagerDeliveryEngineV1.notify_auto_client_request(
            request_number=request_number,
            request_type=request_type,
            description=description,
            client_username=client_username,
            client_full_name=client_full_name,
            photo_file_id=photo_file_id,
        )
