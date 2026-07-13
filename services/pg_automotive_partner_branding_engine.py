# Automotive Partner Branding UI v1 — branded cards, CTAs, lead intake.

from __future__ import annotations

import uuid
from typing import Any

from database.models.automotive_partner_integration import AutomotivePartnerType
from database.models.lead_automation_engine import AutomationLeadSource
from database.session import get_session
from repositories.automotive_partner_repository import AutomotivePartnerRepository
from services.pg_lead_automation_engine import LeadAutomationEngineV1
from services.tenant_context import TenantContextService


class AutomotivePartnerBrandingError(Exception):
    pass


CATEGORY_LABELS = {
    AutomotivePartnerType.INSURANCE.value: "🛡 Insurance",
    AutomotivePartnerType.CREDIT.value: "🏦 Credit",
    AutomotivePartnerType.LEASING.value: "💳 Leasing",
    AutomotivePartnerType.LOGISTICS.value: "🚚 Logistics",
    AutomotivePartnerType.LEGAL.value: "⚖ Legal",
}


class AutomotivePartnerBrandingEngineV1:
    @staticmethod
    def _partner_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "partner_type": row.partner_type,
            "website": row.website,
            "telegram_channel": row.telegram_channel,
        }

    @staticmethod
    def _branding_snapshot(row) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "card_title": row.card_title,
            "short_description": row.short_description,
            "logo_url": row.logo_url,
            "logo_file_id": row.logo_file_id,
            "logo_emoji": row.logo_emoji,
            "logo_enabled": row.logo_enabled,
            "sort_order": row.sort_order,
        }

    @staticmethod
    def _cta_snapshot(row) -> dict[str, Any]:
        return {
            "cta_code": row.cta_code,
            "label": row.label,
            "action_type": row.action_type,
            "action_value": row.action_value,
            "sort_order": row.sort_order,
        }

    @staticmethod
    async def list_category_cards(
        category: str,
        *,
        actor_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            partners = await repo.list_partners(partner_type=category)
            cards: list[dict[str, Any]] = []
            for partner in partners:
                branding = await repo.get_branding(partner.id)
                ctas = await repo.list_ctas(partner.id)
                card = {
                    **AutomotivePartnerBrandingEngineV1._partner_snapshot(partner),
                    "branding": AutomotivePartnerBrandingEngineV1._branding_snapshot(branding),
                    "ctas": [
                        AutomotivePartnerBrandingEngineV1._cta_snapshot(c) for c in ctas
                    ],
                }
                cards.append(card)
            cards.sort(key=lambda item: item.get("branding", {}).get("sort_order", 0))
        return cards

    @staticmethod
    async def get_partner_card(
        partner_code: str,
        *,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise AutomotivePartnerBrandingError(f"Partner {partner_code} not found")
            branding = await repo.get_branding(partner.id)
            ctas = await repo.list_ctas(partner.id)
            products = await repo.list_products_for_partner(partner.id)
        return {
            **AutomotivePartnerBrandingEngineV1._partner_snapshot(partner),
            "branding": AutomotivePartnerBrandingEngineV1._branding_snapshot(branding),
            "ctas": [AutomotivePartnerBrandingEngineV1._cta_snapshot(c) for c in ctas],
            "products": [
                {
                    "product_code": p.product_code,
                    "name": p.name,
                    "description": p.description,
                }
                for p in products
            ],
        }

    @staticmethod
    def format_category_header(category: str) -> str:
        label = CATEGORY_LABELS.get(category, category.title())
        return f"{label}\n\nSelect a partner:"

    @staticmethod
    def format_partner_card_text(card: dict[str, Any]) -> str:
        branding = card.get("branding") or {}
        emoji = branding.get("logo_emoji") or "🤝"
        title = branding.get("card_title") or card.get("name", "Partner")
        lines = [f"{emoji} {title}", ""]
        if branding.get("short_description"):
            lines.append(branding["short_description"])
        elif card.get("website"):
            lines.append(f"Official partner — {card['website']}")
        lines.append("")
        lines.append(f"Partner: {card.get('name', '—')}")
        if card.get("website"):
            lines.append(f"🌐 {card['website']}")
        return "\n".join(lines)

    @staticmethod
    def partner_photo(card: dict[str, Any]) -> str | None:
        branding = card.get("branding") or {}
        if not branding.get("logo_enabled"):
            return None
        return branding.get("logo_file_id") or branding.get("logo_url")

    @staticmethod
    async def create_partner_lead(
        *,
        partner_code: str,
        actor_id: int,
        customer_name: str,
        phone: str | None = None,
        notes: str | None = None,
        cta_code: str | None = None,
    ) -> dict[str, Any]:
        card = await AutomotivePartnerBrandingEngineV1.get_partner_card(partner_code, actor_id=actor_id)
        lead_notes = notes or f"Partner lead: {card['name']} ({card['partner_type']})"
        if cta_code:
            lead_notes += f" — CTA: {cta_code}"
        return await LeadAutomationEngineV1.ingest_lead(
            source=AutomationLeadSource.TELEGRAM.value,
            customer_name=customer_name,
            phone=phone,
            telegram_user_id=actor_id,
            notes=lead_notes,
            actor_id=actor_id,
            source_metadata={
                "partner_code": partner_code,
                "partner_type": card["partner_type"],
                "cta_code": cta_code,
                "channel": "automotive_partner_branding_v1",
            },
            external_reference=f"partner:{partner_code}:{actor_id}",
        )

    @staticmethod
    async def branding_health() -> dict[str, Any]:
        required = {
            AutomotivePartnerType.INSURANCE.value: {"sgtas"},
            AutomotivePartnerType.CREDIT.value: {"credit_agricole", "privatbank"},
            AutomotivePartnerType.LEASING.value: {"eco_leasing"},
            AutomotivePartnerType.LOGISTICS.value: {"smart_auto_cargo"},
            AutomotivePartnerType.LEGAL.value: {"bidex_legal"},
        }
        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            report: dict[str, Any] = {"categories": {}, "ok": True}
            for category, codes in required.items():
                partners = await repo.list_partners(partner_type=category)
                found = {p.code for p in partners}
                branded = 0
                for partner in partners:
                    if await repo.get_branding(partner.id):
                        branded += 1
                missing = codes - found
                report["categories"][category] = {
                    "partners": len(partners),
                    "branded": branded,
                    "missing": sorted(missing),
                }
                if missing or branded < len(codes):
                    report["ok"] = False
        return report
