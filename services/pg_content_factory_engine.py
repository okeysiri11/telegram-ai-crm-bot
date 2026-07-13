# Content Factory Engine v1 — AI-generated car marketing content.

from __future__ import annotations

import uuid
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.content_factory_engine import ContentType
from database.session import get_session
from openrouter import ask_openrouter
from repositories.audit_repository import AuditRepository
from repositories.content_factory_repository import ContentFactoryRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_car_engine import CarEngineError, CarEngineV1

CONTENT_FACTORY_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

CONTENT_PROMPTS: dict[str, str] = {
    ContentType.CAR_DESCRIPTION.value: (
        "Write a compelling car listing description (150-250 words) for a dealership. "
        "Highlight condition, value, and call to action. Language: Russian."
    ),
    ContentType.TELEGRAM_POST.value: (
        "Write a Telegram channel post (max 900 chars) with emoji. "
        "Include VIN, price, key specs. Language: Russian."
    ),
    ContentType.INSTAGRAM_POST.value: (
        "Write an Instagram caption (max 2200 chars) with hashtags. "
        "Engaging tone, line breaks, 8-12 hashtags. Language: Russian."
    ),
    ContentType.TIKTOK_SCRIPT.value: (
        "Write a 30-45 second TikTok video script with hook, features, CTA. "
        "Format: SCENE / VOICEOVER lines. Language: Russian."
    ),
    ContentType.FACEBOOK_AD.value: (
        "Write a Facebook ad: headline (max 40 chars), primary text (max 125 chars), "
        "description (max 30 chars). Language: Russian."
    ),
    ContentType.SEO_TEXT.value: (
        "Write SEO-optimized text (200-300 words) with natural keywords for "
        "make, model, year, for sale. Language: Russian."
    ),
}


class ContentFactoryEngineError(Exception):
    pass


class ContentFactoryEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in CONTENT_FACTORY_ROLES for role in roles)

    @staticmethod
    def _car_context(car: dict[str, Any]) -> str:
        return (
            f"Make: {car.get('make')}\n"
            f"Model: {car.get('model')}\n"
            f"Year: {car.get('year')}\n"
            f"VIN: {car.get('vin')}\n"
            f"Color: {car.get('color') or 'N/A'}\n"
            f"Mileage: {car.get('mileage') or 'N/A'}\n"
            f"Price: {car.get('sale_price') or car.get('purchase_price') or 'N/A'}\n"
            f"Status: {car.get('status')}"
        )

    @staticmethod
    async def _generate(
        actor_id: int,
        car_id: uuid.UUID,
        content_type: str,
    ) -> dict[str, Any]:
        if not await ContentFactoryEngineV1.user_can_access(actor_id):
            raise ContentFactoryEngineError("Access denied")

        try:
            car = await CarEngineV1.get_car(actor_id, car_id)
        except CarEngineError as exc:
            raise ContentFactoryEngineError(str(exc)) from exc

        prompt = CONTENT_PROMPTS.get(content_type)
        if not prompt:
            raise ContentFactoryEngineError(f"Unknown content type: {content_type}")

        user_prompt = (
            f"{prompt}\n\nVehicle data:\n{ContentFactoryEngineV1._car_context(car)}"
        )
        body = await ask_openrouter(
            [{"role": "user", "content": user_prompt}],
            ai_settings={"language": "ru", "tone": "friendly"},
        )

        title = f"{car.get('year')} {car.get('make')} {car.get('model')} — {content_type}"

        async with get_session() as session:
            item = await ContentFactoryRepository(session).create(
                car_id=car_id,
                content_type=content_type,
                title=title,
                body=body.strip(),
                metadata={"vin": car.get("vin"), "model": car.get("model")},
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="content_item",
                entity_id=str(item.id),
                action=AuditAction.CREATE.value,
                new_value={"content_type": content_type, "car_id": str(car_id)},
            )
            await session.refresh(item)
            return ContentFactoryRepository.snapshot(item)

    @staticmethod
    async def generate_car_description(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.CAR_DESCRIPTION.value
        )

    @staticmethod
    async def generate_telegram_post(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.TELEGRAM_POST.value
        )

    @staticmethod
    async def generate_instagram_post(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.INSTAGRAM_POST.value
        )

    @staticmethod
    async def generate_tiktok_script(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.TIKTOK_SCRIPT.value
        )

    @staticmethod
    async def generate_facebook_ad(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.FACEBOOK_AD.value
        )

    @staticmethod
    async def generate_seo_text(actor_id: int, car_id: uuid.UUID) -> dict[str, Any]:
        return await ContentFactoryEngineV1._generate(
            actor_id, car_id, ContentType.SEO_TEXT.value
        )

    @staticmethod
    async def generate_all(actor_id: int, car_id: uuid.UUID) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for content_type in ContentType:
            item = await ContentFactoryEngineV1._generate(actor_id, car_id, content_type.value)
            results.append(item)
        return results

    @staticmethod
    async def list_content(
        actor_id: int,
        car_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if not await ContentFactoryEngineV1.user_can_access(actor_id):
            raise ContentFactoryEngineError("Access denied")

        async with get_session() as session:
            items = await ContentFactoryRepository(session).list_for_car(car_id)
            return [ContentFactoryRepository.snapshot(i) for i in items]
