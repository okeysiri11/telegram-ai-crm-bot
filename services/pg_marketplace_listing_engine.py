# Marketplace listing generator — structured listings from client requests.

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from database.models.marketplace_listing import MarketplaceListingStatus
from database.session import get_session

logger = logging.getLogger(__name__)


class MarketplaceListingEngineV1:
    @staticmethod
    def build_listing_payload(data: dict[str, Any]) -> dict[str, Any]:
        user_desc = (data.get("user_description") or data.get("description") or "").strip()
        fuel = data.get("fuel") or MarketplaceListingEngineV1._extract_field(user_desc, "fuel")
        city = data.get("city") or MarketplaceListingEngineV1._extract_field(user_desc, "city")
        return {
            "brand": data.get("brand"),
            "model": data.get("model"),
            "year": data.get("year"),
            "price": data.get("price"),
            "fuel": fuel,
            "city": city,
            "mileage": data.get("mileage"),
            "vin": data.get("vin"),
            "description": user_desc or None,
        }

    @staticmethod
    async def create_from_client_request(
        *,
        client_request_id: uuid.UUID,
        seller_telegram_id: int,
        seller_username: str | None,
        data: dict[str, Any],
        photo_file_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = MarketplaceListingEngineV1.build_listing_payload(data)
        async with get_session() as session:
            from database.models.marketplace_listing import MarketplaceListing

            row = MarketplaceListing(
                status=MarketplaceListingStatus.ACTIVE.value,
                seller_telegram_id=seller_telegram_id,
                seller_username=seller_username,
                brand=payload.get("brand"),
                model=payload.get("model"),
                year=payload.get("year"),
                price=payload.get("price"),
                currency="USD",
                fuel=payload.get("fuel"),
                city=payload.get("city"),
                mileage=payload.get("mileage"),
                vin=payload.get("vin"),
                description=payload.get("description"),
                photo_file_ids=photo_file_ids,
                listing_payload=payload,
                client_request_id=client_request_id,
            )
            session.add(row)
            await session.flush()
            listing_id = row.id

            from sqlalchemy import update
            from database.models.client_request import ClientRequest

            await session.execute(
                update(ClientRequest)
                .where(ClientRequest.id == client_request_id)
                .values(marketplace_listing_id=listing_id)
            )

        logger.info("MARKETPLACE_LISTING created id=%s client_request=%s", listing_id, client_request_id)
        return {"id": str(listing_id), "payload": payload}

    @staticmethod
    def _extract_field(text: str, field: str) -> str | None:
        patterns = {
            "fuel": r"(diesel|бензин|petrol|электро|hybrid|гибрид|дизель)",
            "city": r"(?:город|city)[:\s]+([A-Za-zА-Яа-яІіЇї\-]+)",
        }
        pattern = patterns.get(field)
        if not pattern:
            return None
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return match.group(1) if match.lastindex else match.group(0)
