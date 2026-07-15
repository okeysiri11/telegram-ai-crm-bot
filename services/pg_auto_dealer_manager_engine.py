# Auto dealer default manager — Boris provisioning and lead assignment.

from __future__ import annotations

import logging
import uuid
from typing import Any

from database.models.roles import RbacRole
from database.session import get_session
from repositories.rbac_repository import RbacRepository
from repositories.users_repository import UsersRepository

logger = logging.getLogger(__name__)

BORIS_TELEGRAM_ID = 393792086
BORIS_USERNAME = "Boroda_0003"
BORIS_FULL_NAME = "Борис"
BORIS_ROLE_CODE = "manager"
BORIS_ROLE_NAME = "Manager"
BORIS_ROLE_DESCRIPTION = "CRM manager"


class AutoDealerManagerEngineV1:
    @staticmethod
    def is_auto_dealer_lead(*, source_link: str | None, vertical: str | None) -> bool:
        if source_link in {"auto_dealer", "auto_client"}:
            return True
        return vertical in {"automotive", "auto"}

    @staticmethod
    async def ensure_default_manager() -> uuid.UUID | None:
        try:
            async with get_session() as session:
                user = await UsersRepository(session).ensure_user(
                    telegram_id=BORIS_TELEGRAM_ID,
                    username=BORIS_USERNAME,
                    full_name=BORIS_FULL_NAME,
                    is_active=True,
                )
                rbac = RbacRepository(session)
                role = await rbac.get_role_by_code(BORIS_ROLE_CODE)
                if role is None:
                    role = RbacRole(
                        code=BORIS_ROLE_CODE,
                        name=BORIS_ROLE_NAME,
                        description=BORIS_ROLE_DESCRIPTION,
                    )
                    session.add(role)
                    await session.flush()
                await rbac.assign_role(user.id, BORIS_ROLE_CODE)
                return user.id
        except Exception:
            logger.warning(
                "Auto dealer manager provisioning failed for telegram_id=%s",
                BORIS_TELEGRAM_ID,
                exc_info=True,
            )
            return None

    @staticmethod
    async def resolve_manager_uuid() -> uuid.UUID | None:
        async with get_session() as session:
            user = await UsersRepository(session).get_by_telegram_id(BORIS_TELEGRAM_ID)
            if user is None:
                return None
            return user.id

    @staticmethod
    async def auto_assign_dealer_lead(snapshot: dict[str, Any]) -> dict[str, Any] | None:
        if not AutoDealerManagerEngineV1.is_auto_dealer_lead(
            source_link=snapshot.get("source_link"),
            vertical=snapshot.get("vertical"),
        ):
            return None

        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        try:
            lead_id = uuid.UUID(str(snapshot["id"]))
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "AUTO DEALER: invalid lead id in snapshot — assignment skipped: %s",
                snapshot.get("id"),
            )
            return snapshot

        return await ManagerDeliveryEngineV1.assign_lead_manager(
            lead_id=lead_id,
            snapshot=snapshot,
        )

    @staticmethod
    def request_type_label(request_type: str | None) -> str:
        labels = {
            "buy_car": "🚗 Поиск автомобиля",
            "sell_car": "💰 Продажа автомобиля",
            "listing": "📢 Размещение объявления",
            "manager_callback": "📞 Связаться с менеджером",
        }
        return labels.get(request_type or "", request_type or "—")

    @staticmethod
    async def notify_manager_for_lead(snapshot: dict[str, Any]) -> None:
        from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

        request_type = snapshot.get("client_request_type") or "buy_car"
        db_type_map = {
            "buy_car": "AUTO_SEARCH",
            "sell_car": "AUTO_SELL",
            "listing": "AUTO_LISTING",
            "manager_callback": "AUTO_MANAGER_CALLBACK",
        }
        await ManagerDeliveryEngineV1.notify_auto_client_request(
            request_number=str(snapshot.get("id", ""))[:8],
            request_type=db_type_map.get(request_type, request_type),
            description=snapshot.get("client_description"),
            client_username=snapshot.get("telegram_username"),
            client_full_name=snapshot.get("full_name"),
            photo_file_id=snapshot.get("client_photo_file_id"),
            lead_id=snapshot.get("id"),
        )
