# VIN Engine v1 repository.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.vin_report import VinReport
from services.vin_decoder import decode_vin, validate_vin


class VinRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_vin(self, vin: str) -> VinReport | None:
        normalized = vin.strip().upper()
        result = await self._session.execute(
            select(VinReport).where(VinReport.vin == normalized)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, report_id: uuid.UUID) -> VinReport | None:
        result = await self._session.execute(
            select(VinReport).where(VinReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def create_report(
        self,
        *,
        vin: str,
        car_id: uuid.UUID | None = None,
        is_valid: bool,
        decoded_data: dict | None = None,
        vehicle_history: list | None = None,
        auction_references: list | None = None,
        validation_errors: list | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> VinReport:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        normalized = vin.strip().upper()
        report = VinReport(
            vin=normalized,
            car_id=car_id,
            is_valid=is_valid,
            decoded_data=decoded_data,
            vehicle_history=vehicle_history or [],
            auction_references=auction_references or [],
            validation_errors=validation_errors,
            created_by=created_by,
        )
        self._session.add(report)
        await self._session.flush()
        return report

    async def upsert_from_decoder(
        self,
        vin: str,
        *,
        car_id: uuid.UUID | None = None,
        created_by: int | None = None,
    ) -> VinReport:
        decoded = decode_vin(vin)
        normalized = decoded["vin"]
        existing = await self.get_by_vin(normalized)

        if existing is None:
            return await self.create_report(
                vin=normalized,
                car_id=car_id,
                is_valid=decoded["is_valid"],
                decoded_data=decoded.get("decoded"),
                validation_errors=decoded.get("errors") or None,
                created_by=created_by,
            )

        existing.is_valid = decoded["is_valid"]
        existing.decoded_data = decoded.get("decoded")
        existing.validation_errors = decoded.get("errors") or None
        if car_id is not None:
            existing.car_id = car_id
        await self._session.flush()
        return existing

    async def append_history(
        self,
        vin: str,
        event: dict[str, Any],
    ) -> VinReport | None:
        report = await self.get_by_vin(vin)
        if report is None:
            return None
        history = list(report.vehicle_history or [])
        history.append(event)
        report.vehicle_history = history
        await self._session.flush()
        return report

    async def add_auction_reference(
        self,
        vin: str,
        reference: dict[str, Any],
    ) -> VinReport | None:
        report = await self.get_by_vin(vin)
        if report is None:
            return None
        refs = list(report.auction_references or [])
        refs.append(reference)
        report.auction_references = refs
        await self._session.flush()
        return report

    async def link_car(
        self,
        vin: str,
        car_id: uuid.UUID,
    ) -> VinReport | None:
        report = await self.get_by_vin(vin)
        if report is None:
            return None
        report.car_id = car_id
        await self._session.flush()
        return report

    @staticmethod
    def snapshot(report: VinReport) -> dict[str, Any]:
        return {
            "id": str(report.id),
            "vin": report.vin,
            "car_id": str(report.car_id) if report.car_id else None,
            "is_valid": report.is_valid,
            "decoded_data": report.decoded_data,
            "vehicle_history": report.vehicle_history or [],
            "auction_references": report.auction_references or [],
            "validation_errors": report.validation_errors or [],
            "created_by": report.created_by,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        }
