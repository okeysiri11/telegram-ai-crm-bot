# Anti Loss Layer v1 repository.

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.anti_loss_layer_v1 import (
    AntiLossEntityType,
    AntiLossEventType,
    AntiLossFingerprintType,
    AntiLossLayerV1Event,
    AntiLossLayerV1Fingerprint,
)
from database.models.deal_engine_v1 import (
    DEAL_ENGINE_V1_TERMINAL_STATUSES,
    DealEngineV1Deal,
)
from database.models.lead_engine import LEAD_ENGINE_TERMINAL_STATUSES, LeadEngineLead


class AntiLossLayerV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_fingerprint(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        vertical: str,
        fingerprint_type: str,
        fingerprint_value: str,
    ) -> AntiLossLayerV1Fingerprint | None:
        existing = await self.find_by_fingerprint(
            vertical=vertical,
            fingerprint_type=fingerprint_type,
            fingerprint_value=fingerprint_value,
        )
        if existing is not None:
            return existing
        row = AntiLossLayerV1Fingerprint(
            entity_type=entity_type,
            entity_id=entity_id,
            vertical=vertical,
            fingerprint_type=fingerprint_type,
            fingerprint_value=fingerprint_value,
            is_active=True,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def find_by_fingerprint(
        self,
        *,
        vertical: str,
        fingerprint_type: str,
        fingerprint_value: str,
        entity_type: str | None = None,
    ) -> AntiLossLayerV1Fingerprint | None:
        stmt = select(AntiLossLayerV1Fingerprint).where(
            AntiLossLayerV1Fingerprint.vertical == vertical,
            AntiLossLayerV1Fingerprint.fingerprint_type == fingerprint_type,
            AntiLossLayerV1Fingerprint.fingerprint_value == fingerprint_value,
            AntiLossLayerV1Fingerprint.is_active.is_(True),
        )
        if entity_type:
            stmt = stmt.where(AntiLossLayerV1Fingerprint.entity_type == entity_type)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def deactivate_entity_fingerprints(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> None:
        await self._session.execute(
            update(AntiLossLayerV1Fingerprint)
            .where(
                AntiLossLayerV1Fingerprint.entity_type == entity_type,
                AntiLossLayerV1Fingerprint.entity_id == entity_id,
            )
            .values(is_active=False)
        )
        await self._session.flush()

    async def log_event(
        self,
        *,
        event_type: str,
        vertical: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        matched_entity_id: uuid.UUID | None = None,
        match_type: str | None = None,
        details: str | None = None,
        actor_telegram_id: int | None = None,
    ) -> AntiLossLayerV1Event:
        row = AntiLossLayerV1Event(
            event_type=event_type,
            vertical=vertical,
            entity_type=entity_type,
            entity_id=entity_id,
            matched_entity_id=matched_entity_id,
            match_type=match_type,
            details=details,
            actor_telegram_id=actor_telegram_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def count_events(self, event_type: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AntiLossLayerV1Event)
            .where(AntiLossLayerV1Event.event_type == event_type)
        )
        return int(result.scalar_one())

    async def get_lead(self, lead_id: uuid.UUID) -> LeadEngineLead | None:
        result = await self._session.execute(
            select(LeadEngineLead).where(LeadEngineLead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_deal(self, deal_id: uuid.UUID) -> DealEngineV1Deal | None:
        result = await self._session.execute(
            select(DealEngineV1Deal).where(DealEngineV1Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def find_open_lead_by_telegram(
        self,
        vertical: str,
        telegram_user_id: int,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(
                LeadEngineLead.vertical == vertical,
                LeadEngineLead.telegram_user_id == telegram_user_id,
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
                LeadEngineLead.status.not_in(tuple(LEAD_ENGINE_TERMINAL_STATUSES)),
            )
            .order_by(LeadEngineLead.created_at.asc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(LeadEngineLead.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lead_by_phone(
        self,
        vertical: str,
        phone_normalized: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(
                LeadEngineLead.vertical == vertical,
                LeadEngineLead.phone_normalized == phone_normalized,
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
                LeadEngineLead.status.not_in(tuple(LEAD_ENGINE_TERMINAL_STATUSES)),
            )
            .order_by(LeadEngineLead.created_at.asc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(LeadEngineLead.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lead_by_vin(
        self,
        vin: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(
                LeadEngineLead.vertical == "auto",
                LeadEngineLead.vin == vin,
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
                LeadEngineLead.status.not_in(tuple(LEAD_ENGINE_TERMINAL_STATUSES)),
            )
            .order_by(LeadEngineLead.created_at.asc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(LeadEngineLead.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lead_by_registration(
        self,
        registration: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(
                LeadEngineLead.vertical == "auto",
                LeadEngineLead.vehicle_registration == registration,
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
                LeadEngineLead.status.not_in(tuple(LEAD_ENGINE_TERMINAL_STATUSES)),
            )
            .order_by(LeadEngineLead.created_at.asc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(LeadEngineLead.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lead_by_agro_bundle(
        self,
        *,
        product: str,
        volume: str,
        location: str,
        exclude_id: uuid.UUID | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(
                LeadEngineLead.vertical == "agro",
                LeadEngineLead.agro_product == product,
                LeadEngineLead.agro_volume == volume,
                LeadEngineLead.agro_location == location,
                LeadEngineLead.is_duplicate.is_(False),
                LeadEngineLead.merged_into_id.is_(None),
                LeadEngineLead.status.not_in(tuple(LEAD_ENGINE_TERMINAL_STATUSES)),
            )
            .order_by(LeadEngineLead.created_at.asc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(LeadEngineLead.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active_deal_for_lead(self, lead_id: uuid.UUID) -> DealEngineV1Deal | None:
        result = await self._session.execute(
            select(DealEngineV1Deal)
            .where(
                DealEngineV1Deal.lead_id == lead_id,
                DealEngineV1Deal.is_duplicate.is_(False),
                DealEngineV1Deal.merged_into_id.is_(None),
                DealEngineV1Deal.status.not_in(tuple(DEAL_ENGINE_V1_TERMINAL_STATUSES)),
            )
            .order_by(DealEngineV1Deal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_active_deal_for_client(
        self,
        *,
        vertical: str,
        client_id: uuid.UUID,
        title: str,
        exclude_id: uuid.UUID | None = None,
    ) -> DealEngineV1Deal | None:
        stmt = (
            select(DealEngineV1Deal)
            .where(
                DealEngineV1Deal.vertical == vertical,
                DealEngineV1Deal.client_id == client_id,
                DealEngineV1Deal.title == title,
                DealEngineV1Deal.is_duplicate.is_(False),
                DealEngineV1Deal.merged_into_id.is_(None),
                DealEngineV1Deal.status.not_in(tuple(DEAL_ENGINE_V1_TERMINAL_STATUSES)),
            )
            .order_by(DealEngineV1Deal.created_at.desc())
            .limit(1)
        )
        if exclude_id:
            stmt = stmt.where(DealEngineV1Deal.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_lead(self, lead_id: uuid.UUID, **fields) -> LeadEngineLead | None:
        row = await self.get_lead(lead_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def update_deal(self, deal_id: uuid.UUID, **fields) -> DealEngineV1Deal | None:
        row = await self.get_deal(deal_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def recent_events(self, *, limit: int = 10) -> list[AntiLossLayerV1Event]:
        result = await self._session.execute(
            select(AntiLossLayerV1Event)
            .order_by(AntiLossLayerV1Event.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
