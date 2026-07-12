# Automotive Inventory Engine v1 — vehicle inventory management.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.automotive_inventory import VehicleStatus
from database.session import get_session
from repositories.automotive_inventory_repository import (
    VehicleDocumentRepository,
    VehicleImageRepository,
    VehicleLocationRepository,
    VehicleRepository,
    VehicleStatusHistoryRepository,
)
from repositories.user_role_repository import UserRoleRepository

INVENTORY_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AutomotiveInventoryEngineError(Exception):
    pass


class AutomotiveInventoryEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in INVENTORY_ROLES for role in roles)

    @staticmethod
    def _vehicle_snapshot(vehicle) -> dict[str, Any]:
        return {
            "id": str(vehicle.id),
            "vin": vehicle.vin,
            "stock_number": vehicle.stock_number,
            "make": vehicle.make,
            "model": vehicle.model,
            "generation": vehicle.generation,
            "year": vehicle.year,
            "engine": vehicle.engine,
            "fuel_type": vehicle.fuel_type,
            "transmission": vehicle.transmission,
            "drivetrain": vehicle.drivetrain,
            "color": vehicle.color,
            "mileage": vehicle.mileage,
            "purchase_price": str(vehicle.purchase_price) if vehicle.purchase_price else None,
            "target_price": str(vehicle.target_price) if vehicle.target_price else None,
            "sale_price": str(vehicle.sale_price) if vehicle.sale_price else None,
            "currency": vehicle.currency,
            "status": vehicle.status,
            "created_at": vehicle.created_at.isoformat(),
            "updated_at": vehicle.updated_at.isoformat(),
        }

    @staticmethod
    async def create_vehicle(
        actor_id: int,
        *,
        vin: str,
        stock_number: str,
        make: str,
        model: str,
        year: int,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            repo = VehicleRepository(session)
            if await repo.get_by_vin(vin):
                raise AutomotiveInventoryEngineError(f"Vehicle with VIN already exists: {vin}")

            vehicle = await repo.create(
                vin=vin,
                stock_number=stock_number,
                make=make,
                model=model,
                year=year,
                **fields,
            )
            await VehicleStatusHistoryRepository(session).record(
                vehicle_id=vehicle.id,
                to_status=vehicle.status,
                changed_by=actor_id,
                notes="Vehicle created",
            )
            return AutomotiveInventoryEngineV1._vehicle_snapshot(vehicle)

    @staticmethod
    async def update_vehicle(
        actor_id: int,
        vehicle_id: uuid.UUID,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).update_fields(vehicle_id, **fields)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")
            return AutomotiveInventoryEngineV1._vehicle_snapshot(vehicle)

    @staticmethod
    async def update_status(
        actor_id: int,
        vehicle_id: uuid.UUID,
        status: str,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")
        if status not in {s.value for s in VehicleStatus}:
            raise AutomotiveInventoryEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            repo = VehicleRepository(session)
            vehicle = await repo.get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")

            old_status = vehicle.status
            vehicle = await repo.update_status(vehicle_id, status)
            await VehicleStatusHistoryRepository(session).record(
                vehicle_id=vehicle_id,
                from_status=old_status,
                to_status=status,
                changed_by=actor_id,
                notes=notes,
            )
            return AutomotiveInventoryEngineV1._vehicle_snapshot(vehicle)

    @staticmethod
    async def add_image(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        url: str,
        image_type: str | None = None,
        sort_order: int = 0,
        caption: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")

            image = await VehicleImageRepository(session).create(
                vehicle_id=vehicle_id,
                url=url,
                image_type=image_type,
                sort_order=sort_order,
                caption=caption,
            )
            return {
                "id": str(image.id),
                "vehicle_id": str(vehicle_id),
                "url": image.url,
                "image_type": image.image_type,
                "sort_order": image.sort_order,
            }

    @staticmethod
    async def add_document(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        document_type: str,
        file_url: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")

            document = await VehicleDocumentRepository(session).create(
                vehicle_id=vehicle_id,
                document_type=document_type,
                file_url=file_url,
                notes=notes,
            )
            return {
                "id": str(document.id),
                "vehicle_id": str(vehicle_id),
                "document_type": document.document_type,
                "file_url": document.file_url,
                "status": document.status,
            }

    @staticmethod
    async def record_location(
        actor_id: int,
        vehicle_id: uuid.UUID,
        *,
        location_type: str,
        location_name: str,
        country: str | None = None,
        city: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")

            location = await VehicleLocationRepository(session).create(
                vehicle_id=vehicle_id,
                location_type=location_type,
                location_name=location_name,
                country=country,
                city=city,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
            )

            status_map = {
                "PORT": VehicleStatus.AT_PORT.value,
                "CUSTOMS": VehicleStatus.IN_CUSTOMS.value,
                "WAREHOUSE": VehicleStatus.IN_STOCK.value,
                "TRANSIT": VehicleStatus.IN_TRANSIT.value,
            }
            new_status = status_map.get(location_type.upper())
            if new_status and vehicle.status != new_status:
                old_status = vehicle.status
                await VehicleRepository(session).update_status(vehicle_id, new_status)
                await VehicleStatusHistoryRepository(session).record(
                    vehicle_id=vehicle_id,
                    from_status=old_status,
                    to_status=new_status,
                    changed_by=actor_id,
                    notes=f"Auto-updated from location: {location_name}",
                )

            return {
                "id": str(location.id),
                "vehicle_id": str(vehicle_id),
                "location_type": location.location_type,
                "location_name": location.location_name,
                "country": location.country,
                "city": location.city,
                "is_current": location.is_current,
            }

    @staticmethod
    async def get_vehicle(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveInventoryEngineError(f"Vehicle not found: {vehicle_id}")

            images = await VehicleImageRepository(session).list_by_vehicle(vehicle_id)
            documents = await VehicleDocumentRepository(session).list_by_vehicle(vehicle_id)
            history = await VehicleStatusHistoryRepository(session).list_by_vehicle(
                vehicle_id
            )
            locations = await VehicleLocationRepository(session).list_by_vehicle(
                vehicle_id
            )
            current = await VehicleLocationRepository(session).get_current(vehicle_id)

            return {
                "vehicle": AutomotiveInventoryEngineV1._vehicle_snapshot(vehicle),
                "current_location": {
                    "location_type": current.location_type,
                    "location_name": current.location_name,
                    "country": current.country,
                    "city": current.city,
                }
                if current
                else None,
                "images": [
                    {
                        "id": str(i.id),
                        "url": i.url,
                        "image_type": i.image_type,
                        "sort_order": i.sort_order,
                    }
                    for i in images
                ],
                "documents": [
                    {
                        "id": str(d.id),
                        "document_type": d.document_type,
                        "file_url": d.file_url,
                        "status": d.status,
                    }
                    for d in documents
                ],
                "status_history": [
                    {
                        "from_status": h.from_status,
                        "to_status": h.to_status,
                        "created_at": h.created_at.isoformat(),
                        "notes": h.notes,
                    }
                    for h in history
                ],
                "locations": [
                    {
                        "id": str(loc.id),
                        "location_type": loc.location_type,
                        "location_name": loc.location_name,
                        "is_current": loc.is_current,
                        "arrived_at": loc.arrived_at.isoformat() if loc.arrived_at else None,
                    }
                    for loc in locations
                ],
            }

    @staticmethod
    async def list_vehicles(
        actor_id: int,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveInventoryEngineV1.user_can_access(actor_id):
            raise AutomotiveInventoryEngineError("Access denied")

        async with get_session() as session:
            repo = VehicleRepository(session)
            if status:
                vehicles = await repo.list_by_status(status, limit=limit)
            else:
                vehicles = await repo.list_all(limit=limit)

            return [
                AutomotiveInventoryEngineV1._vehicle_snapshot(v) for v in vehicles
            ]
