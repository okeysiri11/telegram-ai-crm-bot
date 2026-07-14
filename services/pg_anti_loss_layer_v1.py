# Anti Loss Layer v1 — duplicate prevention, merge, owner metrics.

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from database.models.anti_loss_layer_v1 import (
    AntiLossEntityType,
    AntiLossEventType,
    AntiLossFingerprintType,
)
from database.models.deal_engine_v1 import DealEngineV1Status
from database.session import get_session
from repositories.anti_loss_layer_v1_repository import AntiLossLayerV1Repository

logger = logging.getLogger(__name__)


class AntiLossLayerV1Error(Exception):
    pass


class AntiLossLayerV1:
    @staticmethod
    def normalize_phone(phone: str | None) -> str | None:
        if not phone:
            return None
        digits = re.sub(r"\D", "", phone.strip())
        return digits or None

    @staticmethod
    def normalize_vin(vin: str | None) -> str | None:
        if not vin:
            return None
        cleaned = re.sub(r"[^A-Za-z0-9]", "", vin.strip().upper())
        return cleaned or None

    @staticmethod
    def normalize_registration(reg: str | None) -> str | None:
        if not reg:
            return None
        cleaned = re.sub(r"\s+", "", reg.strip().upper())
        return cleaned or None

    @staticmethod
    def normalize_agro_text(value: str | None) -> str | None:
        if not value:
            return None
        cleaned = re.sub(r"\s+", " ", value.strip().lower())
        return cleaned or None

    @staticmethod
    def agro_bundle_value(product: str, volume: str, location: str) -> str:
        return f"{product}|{volume}|{location}"

    @staticmethod
    async def check_lead_duplicate(
        *,
        vertical: str,
        telegram_user_id: int | None = None,
        phone: str | None = None,
        vin: str | None = None,
        vehicle_registration: str | None = None,
        agro_product: str | None = None,
        agro_volume: str | None = None,
        agro_location: str | None = None,
        exclude_lead_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        vertical_key = vertical.strip().lower()
        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)

            checks: list[tuple[str, Any]] = []

            if telegram_user_id is not None:
                match = await repo.find_open_lead_by_telegram(
                    vertical_key,
                    telegram_user_id,
                    exclude_id=exclude_lead_id,
                )
                if match:
                    checks.append((AntiLossFingerprintType.TELEGRAM_ID.value, match))

            phone_norm = AntiLossLayerV1.normalize_phone(phone)
            if phone_norm:
                match = await repo.find_open_lead_by_phone(
                    vertical_key,
                    phone_norm,
                    exclude_id=exclude_lead_id,
                )
                if match:
                    checks.append((AntiLossFingerprintType.PHONE.value, match))

            if vertical_key == "auto":
                vin_norm = AntiLossLayerV1.normalize_vin(vin)
                if vin_norm:
                    match = await repo.find_open_lead_by_vin(vin_norm, exclude_id=exclude_lead_id)
                    if match:
                        checks.append((AntiLossFingerprintType.VIN.value, match))

                reg_norm = AntiLossLayerV1.normalize_registration(vehicle_registration)
                if reg_norm:
                    match = await repo.find_open_lead_by_registration(
                        reg_norm,
                        exclude_id=exclude_lead_id,
                    )
                    if match:
                        checks.append((
                            AntiLossFingerprintType.VEHICLE_REGISTRATION.value,
                            match,
                        ))

            if vertical_key == "agro":
                product = AntiLossLayerV1.normalize_agro_text(agro_product)
                volume = AntiLossLayerV1.normalize_agro_text(agro_volume)
                location = AntiLossLayerV1.normalize_agro_text(agro_location)
                if product and volume and location:
                    match = await repo.find_open_lead_by_agro_bundle(
                        product=product,
                        volume=volume,
                        location=location,
                        exclude_id=exclude_lead_id,
                    )
                    if match:
                        checks.append((AntiLossFingerprintType.AGRO_BUNDLE.value, match))

        if not checks:
            return {"duplicate": False}

        match_type, matched_lead = checks[0]
        return {
            "duplicate": True,
            "match_type": match_type,
            "matched_lead_id": str(matched_lead.id),
            "matched_lead": matched_lead,
        }

    @staticmethod
    async def register_lead_fingerprints(
        lead_id: uuid.UUID,
        *,
        vertical: str,
        telegram_user_id: int | None = None,
        phone: str | None = None,
        vin: str | None = None,
        vehicle_registration: str | None = None,
        agro_product: str | None = None,
        agro_volume: str | None = None,
        agro_location: str | None = None,
    ) -> None:
        vertical_key = vertical.strip().lower()
        try:
            async with get_session() as session:
                repo = AntiLossLayerV1Repository(session)
                if telegram_user_id is not None:
                    await repo.add_fingerprint(
                        entity_type=AntiLossEntityType.LEAD.value,
                        entity_id=lead_id,
                        vertical=vertical_key,
                        fingerprint_type=AntiLossFingerprintType.TELEGRAM_ID.value,
                        fingerprint_value=str(telegram_user_id),
                    )
                phone_norm = AntiLossLayerV1.normalize_phone(phone)
                if phone_norm:
                    await repo.add_fingerprint(
                        entity_type=AntiLossEntityType.LEAD.value,
                        entity_id=lead_id,
                        vertical=vertical_key,
                        fingerprint_type=AntiLossFingerprintType.PHONE.value,
                        fingerprint_value=phone_norm,
                    )
                if vertical_key == "auto":
                    vin_norm = AntiLossLayerV1.normalize_vin(vin)
                    if vin_norm:
                        await repo.add_fingerprint(
                            entity_type=AntiLossEntityType.LEAD.value,
                            entity_id=lead_id,
                            vertical=vertical_key,
                            fingerprint_type=AntiLossFingerprintType.VIN.value,
                            fingerprint_value=vin_norm,
                        )
                    reg_norm = AntiLossLayerV1.normalize_registration(vehicle_registration)
                    if reg_norm:
                        await repo.add_fingerprint(
                            entity_type=AntiLossEntityType.LEAD.value,
                            entity_id=lead_id,
                            vertical=vertical_key,
                            fingerprint_type=AntiLossFingerprintType.VEHICLE_REGISTRATION.value,
                            fingerprint_value=reg_norm,
                        )
                if vertical_key == "agro":
                    product = AntiLossLayerV1.normalize_agro_text(agro_product)
                    volume = AntiLossLayerV1.normalize_agro_text(agro_volume)
                    location = AntiLossLayerV1.normalize_agro_text(agro_location)
                    if product and volume and location:
                        bundle = AntiLossLayerV1.agro_bundle_value(product, volume, location)
                        await repo.add_fingerprint(
                            entity_type=AntiLossEntityType.LEAD.value,
                            entity_id=lead_id,
                            vertical=vertical_key,
                            fingerprint_type=AntiLossFingerprintType.AGRO_BUNDLE.value,
                            fingerprint_value=bundle,
                        )
        except Exception:
            logger.exception("Anti-loss register fingerprints failed lead=%s", lead_id)

    @staticmethod
    async def log_lead_duplicate_prevented(
        *,
        vertical: str,
        matched_lead_id: uuid.UUID,
        match_type: str,
        attempted_telegram_id: int | None = None,
    ) -> None:
        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            await repo.log_event(
                event_type=AntiLossEventType.LEAD_DUPLICATE_PREVENTED.value,
                vertical=vertical,
                entity_type=AntiLossEntityType.LEAD.value,
                matched_entity_id=matched_lead_id,
                match_type=match_type,
                details=f"telegram={attempted_telegram_id}",
                actor_telegram_id=attempted_telegram_id,
            )

    @staticmethod
    async def log_deal_duplicate_prevented(
        *,
        vertical: str,
        matched_deal_id: uuid.UUID,
        match_type: str,
        lead_id: uuid.UUID | None = None,
    ) -> None:
        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            await repo.log_event(
                event_type=AntiLossEventType.DEAL_DUPLICATE_PREVENTED.value,
                vertical=vertical,
                entity_type=AntiLossEntityType.DEAL.value,
                entity_id=lead_id,
                matched_entity_id=matched_deal_id,
                match_type=match_type,
            )

    @staticmethod
    async def check_active_deal_duplicate(
        *,
        vertical: str,
        client_id: uuid.UUID,
        title: str,
        lead_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            if lead_id is not None:
                by_lead = await repo.find_active_deal_for_lead(lead_id)
                if by_lead is not None:
                    return {
                        "duplicate": True,
                        "match_type": "lead_id",
                        "matched_deal_id": str(by_lead.id),
                        "matched_deal": by_lead,
                    }
            by_client = await repo.find_active_deal_for_client(
                vertical=vertical,
                client_id=client_id,
                title=title,
            )
            if by_client is not None:
                return {
                    "duplicate": True,
                    "match_type": "client_title",
                    "matched_deal_id": str(by_client.id),
                    "matched_deal": by_client,
                }
        return {"duplicate": False}

    @staticmethod
    async def merge_leads(
        primary_id: uuid.UUID,
        duplicate_id: uuid.UUID,
        *,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        if primary_id == duplicate_id:
            raise AntiLossLayerV1Error("Cannot merge lead with itself")

        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            primary = await repo.get_lead(primary_id)
            duplicate = await repo.get_lead(duplicate_id)
            if primary is None or duplicate is None:
                raise AntiLossLayerV1Error("Lead not found")
            if primary.vertical != duplicate.vertical:
                raise AntiLossLayerV1Error("Vertical mismatch")

            merge_fields: dict[str, Any] = {}
            for field in (
                "phone",
                "phone_normalized",
                "vin",
                "vehicle_registration",
                "agro_product",
                "agro_volume",
                "agro_location",
                "full_name",
                "telegram_username",
            ):
                if getattr(primary, field) in (None, "") and getattr(duplicate, field):
                    merge_fields[field] = getattr(duplicate, field)

            if merge_fields:
                await repo.update_lead(primary_id, **merge_fields)

            await repo.update_lead(
                duplicate_id,
                is_duplicate=True,
                duplicate_of_id=primary_id,
                merged_into_id=primary_id,
                status="LOST",
            )
            await repo.deactivate_entity_fingerprints(
                AntiLossEntityType.LEAD.value,
                duplicate_id,
            )
            await repo.log_event(
                event_type=AntiLossEventType.LEAD_MERGED.value,
                vertical=primary.vertical,
                entity_type=AntiLossEntityType.LEAD.value,
                entity_id=primary_id,
                matched_entity_id=duplicate_id,
                match_type="manual_merge",
                actor_telegram_id=actor_telegram_id,
            )

            dup_deal = await repo.find_active_deal_for_lead(duplicate_id)
            pri_deal = await repo.find_active_deal_for_lead(primary_id)
            if dup_deal and not pri_deal:
                await repo.update_deal(dup_deal.id, lead_id=primary_id)

        await AntiLossLayerV1.register_lead_fingerprints(
            primary_id,
            vertical=primary.vertical,
            telegram_user_id=primary.telegram_user_id,
            phone=merge_fields.get("phone") or primary.phone,
            vin=merge_fields.get("vin") or primary.vin,
            vehicle_registration=merge_fields.get("vehicle_registration") or primary.vehicle_registration,
            agro_product=merge_fields.get("agro_product") or primary.agro_product,
            agro_volume=merge_fields.get("agro_volume") or primary.agro_volume,
            agro_location=merge_fields.get("agro_location") or primary.agro_location,
        )

        return {
            "primary_id": str(primary_id),
            "duplicate_id": str(duplicate_id),
            "vertical": primary.vertical,
            "merged_fields": list(merge_fields.keys()),
        }

    @staticmethod
    async def merge_deals(
        primary_id: uuid.UUID,
        duplicate_id: uuid.UUID,
        *,
        actor_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        if primary_id == duplicate_id:
            raise AntiLossLayerV1Error("Cannot merge deal with itself")

        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            primary = await repo.get_deal(primary_id)
            duplicate = await repo.get_deal(duplicate_id)
            if primary is None or duplicate is None:
                raise AntiLossLayerV1Error("Deal not found")
            if primary.vertical != duplicate.vertical:
                raise AntiLossLayerV1Error("Vertical mismatch")

            await repo.update_deal(
                duplicate_id,
                is_duplicate=True,
                duplicate_of_id=primary_id,
                merged_into_id=primary_id,
                status=DealEngineV1Status.CANCELLED.value,
            )
            await repo.deactivate_entity_fingerprints(
                AntiLossEntityType.DEAL.value,
                duplicate_id,
            )
            await repo.log_event(
                event_type=AntiLossEventType.DEAL_MERGED.value,
                vertical=primary.vertical,
                entity_type=AntiLossEntityType.DEAL.value,
                entity_id=primary_id,
                matched_entity_id=duplicate_id,
                match_type="manual_merge",
                actor_telegram_id=actor_telegram_id,
            )

        return {
            "primary_id": str(primary_id),
            "duplicate_id": str(duplicate_id),
            "vertical": primary.vertical,
        }

    @staticmethod
    async def get_owner_metrics() -> dict[str, Any]:
        async with get_session() as session:
            repo = AntiLossLayerV1Repository(session)
            leads_prevented = await repo.count_events(
                AntiLossEventType.LEAD_DUPLICATE_PREVENTED.value
            )
            deals_prevented = await repo.count_events(
                AntiLossEventType.DEAL_DUPLICATE_PREVENTED.value
            )
            leads_merged = await repo.count_events(AntiLossEventType.LEAD_MERGED.value)
            deals_merged = await repo.count_events(AntiLossEventType.DEAL_MERGED.value)
            recent = await repo.recent_events(limit=8)

        return {
            "duplicate_leads_prevented": leads_prevented,
            "duplicate_deals_prevented": deals_prevented,
            "leads_merged": leads_merged,
            "deals_merged": deals_merged,
            "recent_events": [
                {
                    "event_type": e.event_type,
                    "vertical": e.vertical,
                    "match_type": e.match_type,
                    "entity_id": str(e.entity_id) if e.entity_id else None,
                    "matched_entity_id": str(e.matched_entity_id) if e.matched_entity_id else None,
                }
                for e in recent
            ],
        }

    @staticmethod
    def format_owner_anti_loss_analytics(data: dict[str, Any]) -> str:
        anti = data.get("anti_loss") or {}
        lines = [
            "🛡 Anti Loss Analytics",
            "",
            f"Duplicate leads prevented: {anti.get('duplicate_leads_prevented', 0)}",
            f"Duplicate deals prevented: {anti.get('duplicate_deals_prevented', 0)}",
            f"Leads merged: {anti.get('leads_merged', 0)}",
            f"Deals merged: {anti.get('deals_merged', 0)}",
            "",
            "AUTO checks: VIN, Phone, Telegram ID, Vehicle registration",
            "AGRO checks: Phone, Telegram ID, Product+Volume+Location",
            "",
            "Recent events:",
        ]
        for event in anti.get("recent_events") or []:
            lines.append(
                f"  • {event['event_type']} ({event.get('vertical', '—')}) "
                f"{event.get('match_type') or ''}"
            )
        if not anti.get("recent_events"):
            lines.append("  • —")
        lines.append("")
        lines.append("Merge commands:")
        lines.append("  /merge_leads <primary_uuid> <duplicate_uuid>")
        lines.append("  /merge_deals <primary_uuid> <duplicate_uuid>")
        return "\n".join(lines)

    @staticmethod
    def lead_snapshot_with_anti_loss(
        row: Any,
        *,
        duplicate_prevented: bool = False,
        match_type: str | None = None,
    ) -> dict[str, Any]:
        from services.pg_lead_engine import LeadEngineV1

        snapshot = LeadEngineV1._snapshot(row)
        snapshot["duplicate_prevented"] = duplicate_prevented
        if match_type:
            snapshot["match_type"] = match_type
        return snapshot
