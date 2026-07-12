# Automotive Inventory Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_inventory import (
    Vehicle,
    VehicleDocument,
    VehicleDocumentStatus,
    VehicleImage,
    VehicleLocation,
    VehicleStatus,
    VehicleStatusHistory,
)


class VehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vin: str,
        stock_number: str,
        make: str,
        model: str,
        year: int,
        generation: str | None = None,
        engine: str | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        drivetrain: str | None = None,
        color: str | None = None,
        mileage: int | None = None,
        purchase_price: Decimal | None = None,
        target_price: Decimal | None = None,
        sale_price: Decimal | None = None,
        currency: str = "USD",
        status: str = VehicleStatus.IN_TRANSIT.value,
        notes: str | None = None,
        **extra: Any,
    ) -> Vehicle:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in VehicleStatus}:
            raise ValueError(f"Invalid status: {status}")
        if year < 1900:
            raise ValueError("year must be >= 1900")

        vehicle = Vehicle(
            vin=vin,
            stock_number=stock_number,
            make=make,
            model=model,
            generation=generation,
            year=year,
            engine=engine,
            fuel_type=fuel_type,
            transmission=transmission,
            drivetrain=drivetrain,
            color=color,
            mileage=mileage,
            purchase_price=purchase_price,
            target_price=target_price,
            sale_price=sale_price,
            currency=currency,
            status=status,
            notes=notes,
        )
        self._session.add(vehicle)
        await self._session.flush()
        return vehicle

    async def get_by_id(self, vehicle_id: uuid.UUID) -> Vehicle | None:
        result = await self._session.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vin(self, vin: str) -> Vehicle | None:
        result = await self._session.execute(
            select(Vehicle).where(Vehicle.vin == vin)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, *, limit: int = 100) -> list[Vehicle]:
        result = await self._session.execute(
            select(Vehicle)
            .where(Vehicle.status == status)
            .order_by(Vehicle.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 100) -> list[Vehicle]:
        result = await self._session.execute(
            select(Vehicle).order_by(Vehicle.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        vehicle_id: uuid.UUID,
        **fields: Any,
    ) -> Vehicle | None:
        vehicle = await self.get_by_id(vehicle_id)
        if vehicle is None:
            return None
        allowed = {
            "make", "model", "generation", "year", "engine", "fuel_type",
            "transmission", "drivetrain", "color", "mileage", "purchase_price",
            "target_price", "sale_price", "currency", "notes",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(vehicle, key, value)
        vehicle.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return vehicle

    async def update_status(
        self,
        vehicle_id: uuid.UUID,
        status: str,
    ) -> Vehicle | None:
        vehicle = await self.get_by_id(vehicle_id)
        if vehicle is None:
            return None
        if status not in {s.value for s in VehicleStatus}:
            raise ValueError(f"Invalid status: {status}")
        vehicle.status = status
        vehicle.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return vehicle


class VehicleImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        url: str,
        image_type: str | None = None,
        sort_order: int = 0,
        caption: str | None = None,
        **extra: Any,
    ) -> VehicleImage:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        image = VehicleImage(
            vehicle_id=vehicle_id,
            url=url,
            image_type=image_type,
            sort_order=sort_order,
            caption=caption,
        )
        self._session.add(image)
        await self._session.flush()
        return image

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleImage]:
        result = await self._session.execute(
            select(VehicleImage)
            .where(VehicleImage.vehicle_id == vehicle_id)
            .order_by(VehicleImage.sort_order.asc(), VehicleImage.created_at.asc())
        )
        return list(result.scalars().all())


class VehicleDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        document_type: str,
        file_url: str,
        status: str = VehicleDocumentStatus.PENDING.value,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleDocument:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in VehicleDocumentStatus}:
            raise ValueError(f"Invalid status: {status}")

        document = VehicleDocument(
            vehicle_id=vehicle_id,
            document_type=document_type,
            file_url=file_url,
            status=status,
            notes=notes,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleDocument]:
        result = await self._session.execute(
            select(VehicleDocument)
            .where(VehicleDocument.vehicle_id == vehicle_id)
            .order_by(VehicleDocument.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: str,
    ) -> VehicleDocument | None:
        result = await self._session.execute(
            select(VehicleDocument).where(VehicleDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            return None
        document.status = status
        await self._session.flush()
        return document


class VehicleStatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        vehicle_id: uuid.UUID,
        to_status: str,
        from_status: str | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> VehicleStatusHistory:
        entry = VehicleStatusHistory(
            vehicle_id=vehicle_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleStatusHistory]:
        result = await self._session.execute(
            select(VehicleStatusHistory)
            .where(VehicleStatusHistory.vehicle_id == vehicle_id)
            .order_by(VehicleStatusHistory.created_at.asc())
        )
        return list(result.scalars().all())


class VehicleLocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vehicle_id: uuid.UUID,
        location_type: str,
        location_name: str,
        country: str | None = None,
        city: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        arrived_at: datetime | None = None,
        is_current: bool = True,
        notes: str | None = None,
        **extra: Any,
    ) -> VehicleLocation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        if is_current:
            await self._session.execute(
                update(VehicleLocation)
                .where(
                    VehicleLocation.vehicle_id == vehicle_id,
                    VehicleLocation.is_current.is_(True),
                )
                .values(is_current=False, departed_at=datetime.now(timezone.utc))
            )

        location = VehicleLocation(
            vehicle_id=vehicle_id,
            location_type=location_type,
            location_name=location_name,
            country=country,
            city=city,
            latitude=latitude,
            longitude=longitude,
            arrived_at=arrived_at or datetime.now(timezone.utc),
            is_current=is_current,
            notes=notes,
        )
        self._session.add(location)
        await self._session.flush()
        return location

    async def get_current(self, vehicle_id: uuid.UUID) -> VehicleLocation | None:
        result = await self._session.execute(
            select(VehicleLocation)
            .where(
                VehicleLocation.vehicle_id == vehicle_id,
                VehicleLocation.is_current.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_vehicle(self, vehicle_id: uuid.UUID) -> list[VehicleLocation]:
        result = await self._session.execute(
            select(VehicleLocation)
            .where(VehicleLocation.vehicle_id == vehicle_id)
            .order_by(VehicleLocation.arrived_at.desc())
        )
        return list(result.scalars().all())
