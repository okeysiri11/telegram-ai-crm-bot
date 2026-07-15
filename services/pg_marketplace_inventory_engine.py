# Marketplace inventory + search + recommendations.

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import and_, func, or_, select

from database.models.marketplace_inventory import InventoryStatus, MarketplaceInventory
from database.session import get_session

logger = logging.getLogger(__name__)


class InventoryEngineV1:
    @staticmethod
    def _snap(row: MarketplaceInventory) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "brand": row.brand,
            "model": row.model,
            "year": row.year,
            "price": float(row.price) if row.price is not None else None,
            "currency": row.currency or "USD",
            "photos": row.photos or [],
            "vin": row.vin,
            "seller_id": row.seller_id,
            "status": row.status,
            "fuel": row.fuel,
            "transmission": row.transmission,
            "mileage": row.mileage,
            "city": row.city,
            "engine": row.engine,
            "description": row.description,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    async def create(**fields: Any) -> dict[str, Any]:
        status = fields.get("status") or InventoryStatus.ACTIVE.value
        async with get_session() as session:
            row = MarketplaceInventory(
                brand=fields.get("brand"),
                model=fields.get("model"),
                year=fields.get("year"),
                price=fields.get("price"),
                currency=fields.get("currency") or "USD",
                photos=fields.get("photos"),
                vin=fields.get("vin"),
                seller_id=fields.get("seller_id"),
                status=status,
                fuel=fields.get("fuel"),
                transmission=fields.get("transmission"),
                mileage=fields.get("mileage"),
                city=fields.get("city"),
                engine=fields.get("engine"),
                description=fields.get("description"),
                marketplace_listing_id=fields.get("marketplace_listing_id"),
            )
            session.add(row)
            await session.flush()
            snap = InventoryEngineV1._snap(row)
            entity_id = str(row.id)

        from services.pg_platform_audit_engine import PlatformAuditEngineV1

        await PlatformAuditEngineV1.log(
            event_type="INVENTORY_CREATED",
            entity_type="inventory",
            entity_id=entity_id,
            user_id=fields.get("seller_id"),
            payload=snap,
        )
        return snap

    @staticmethod
    async def from_listing_payload(
        *,
        seller_id: int,
        payload: dict[str, Any],
        photos: list[str] | None = None,
        marketplace_listing_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        return await InventoryEngineV1.create(
            brand=payload.get("brand"),
            model=payload.get("model"),
            year=payload.get("year"),
            price=payload.get("price"),
            currency=payload.get("currency") or "USD",
            photos=photos or payload.get("photo_file_ids"),
            vin=payload.get("vin"),
            seller_id=seller_id,
            status=InventoryStatus.ACTIVE.value,
            fuel=payload.get("fuel"),
            city=payload.get("city"),
            mileage=payload.get("mileage"),
            description=payload.get("description"),
            marketplace_listing_id=marketplace_listing_id,
        )

    @staticmethod
    async def update_status(item_id: uuid.UUID, status: str) -> dict[str, Any] | None:
        if status not in {s.value for s in InventoryStatus}:
            raise ValueError(f"Invalid status: {status}")
        async with get_session() as session:
            row = await session.get(MarketplaceInventory, item_id)
            if row is None:
                return None
            row.status = status
            await session.flush()
            return InventoryEngineV1._snap(row)

    @staticmethod
    async def search(
        *,
        brand: str | None = None,
        model: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        price_from: float | None = None,
        price_to: float | None = None,
        fuel: str | None = None,
        transmission: str | None = None,
        mileage_max: int | None = None,
        city: str | None = None,
        status: str | None = InventoryStatus.ACTIVE.value,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        filters = []
        if status:
            filters.append(MarketplaceInventory.status == status)
        if brand:
            filters.append(MarketplaceInventory.brand.ilike(f"%{brand}%"))
        if model:
            filters.append(MarketplaceInventory.model.ilike(f"%{model}%"))
        if year_from is not None:
            filters.append(MarketplaceInventory.year >= year_from)
        if year_to is not None:
            filters.append(MarketplaceInventory.year <= year_to)
        if price_from is not None:
            filters.append(MarketplaceInventory.price >= price_from)
        if price_to is not None:
            filters.append(MarketplaceInventory.price <= price_to)
        if fuel:
            filters.append(MarketplaceInventory.fuel.ilike(f"%{fuel}%"))
        if transmission:
            filters.append(MarketplaceInventory.transmission.ilike(f"%{transmission}%"))
        if mileage_max is not None:
            filters.append(MarketplaceInventory.mileage <= mileage_max)
        if city:
            filters.append(MarketplaceInventory.city.ilike(f"%{city}%"))

        async with get_session() as session:
            q = select(MarketplaceInventory)
            if filters:
                q = q.where(and_(*filters))
            q = q.order_by(MarketplaceInventory.created_at.desc()).offset(offset).limit(limit)
            rows = list((await session.execute(q)).scalars().all())
        return [InventoryEngineV1._snap(r) for r in rows]

    @staticmethod
    async def recommend(
        *,
        brand: str | None = None,
        model: str | None = None,
        year: int | None = None,
        price: float | None = None,
        city: str | None = None,
        fuel: str | None = None,
        limit: int = 10,
    ) -> dict[str, list[dict[str, Any]]]:
        """Similar cars / similar listings / alternatives."""
        similar = await InventoryEngineV1.search(
            brand=brand,
            model=model,
            year_from=(year - 2) if year else None,
            year_to=(year + 2) if year else None,
            limit=limit,
        )
        similar_listings = await InventoryEngineV1.search(
            brand=brand,
            price_from=(price * 0.8) if price else None,
            price_to=(price * 1.2) if price else None,
            city=city,
            limit=limit,
        )
        alternatives = await InventoryEngineV1.search(
            fuel=fuel,
            city=city,
            year_from=(year - 3) if year else None,
            year_to=(year + 3) if year else None,
            price_from=(price * 0.7) if price else None,
            price_to=(price * 1.3) if price else None,
            limit=limit * 2,
        )
        # Prefer different model when brand matches for alternatives
        if brand:
            alternatives = [a for a in alternatives if a.get("model") != model][:limit]

        return {
            "similar_cars": similar,
            "similar_listings": similar_listings,
            "alternatives": alternatives,
        }
