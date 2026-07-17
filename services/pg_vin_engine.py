# VIN Engine v1 — business operations for VIN reports and car intake.

from __future__ import annotations

import uuid

from database.session import get_session
from repositories.vin_repository import VinRepository
from services.vin_decoder import build_auction_reference, build_history_event


class VinEngineV1:
    @staticmethod
    async def record_car_intake(
        *,
        vin: str,
        car_id: uuid.UUID,
        created_by: int,
    ) -> None:
        async with get_session() as session:
            repo = VinRepository(session)
            report = await repo.upsert_from_decoder(
                vin,
                car_id=car_id,
                created_by=created_by,
            )
            await repo.append_history(
                vin,
                build_history_event(
                    "car_created",
                    source="telegram",
                    description="Car added via Telegram Cars module",
                    metadata={"car_id": str(car_id)},
                ),
            )
            if not report.auction_references:
                await repo.add_auction_reference(
                    vin,
                    build_auction_reference(
                        "manual_intake",
                        metadata={"channel": "telegram"},
                    ),
                )
