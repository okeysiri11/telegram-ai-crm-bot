# Automotive Partner Integration v1 — partner registry engine.

from __future__ import annotations

import uuid
from typing import Any

from database.models.automotive_partner_integration import (
    AutomotivePartnerType,
    DealerSourceType,
)
from database.session import get_session
from repositories.automotive_partner_repository import AutomotivePartnerRepository
from services.tenant_context import TenantContextService

DEFAULT_INSURANCE_PARTNER_CODE = "sgtas"
DEFAULT_DEALER_PARTNER_CODE = "boroda_cars"


class AutomotivePartnerIntegrationError(Exception):
    pass


class AutomotivePartnerIntegrationEngineV1:
    @staticmethod
    async def _tenant_id_for_actor(actor_id: int) -> uuid.UUID | None:
        try:
            return await TenantContextService.require_tenant_id(actor_id)
        except Exception:
            return None

    @staticmethod
    def _partner_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "code": row.code,
            "name": row.name,
            "partner_type": row.partner_type,
            "website": row.website,
            "telegram_channel": row.telegram_channel,
            "tenant_mode_enabled": row.tenant_mode_enabled,
        }

    @staticmethod
    def _product_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "product_code": row.product_code,
            "name": row.name,
            "description": row.description,
            "external_url": row.external_url,
            "sort_order": row.sort_order,
        }

    @staticmethod
    def _dealer_source_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "partner_id": str(row.partner_id),
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "source_code": row.source_code,
            "source_type": row.source_type,
            "channel_username": row.channel_username,
            "channel_id": row.channel_id,
        }

    @staticmethod
    def _offer_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "partner_id": str(row.partner_id),
            "product_id": str(row.product_id),
            "title": row.title,
            "summary": row.summary,
            "external_url": row.external_url,
            "premium_from": str(row.premium_from) if row.premium_from is not None else None,
            "currency": row.currency,
        }

    @staticmethod
    async def get_insurance_partner(
        *,
        partner_code: str = DEFAULT_INSURANCE_PARTNER_CODE,
    ) -> dict[str, Any]:
        async with get_session() as session:
            partner = await AutomotivePartnerRepository(session).get_partner_by_code(partner_code)
        if partner is None:
            raise AutomotivePartnerIntegrationError(f"Insurance partner {partner_code} not found")
        if partner.partner_type != AutomotivePartnerType.INSURANCE.value:
            raise AutomotivePartnerIntegrationError(f"Partner {partner_code} is not insurance")
        return AutomotivePartnerIntegrationEngineV1._partner_snapshot(partner)

    @staticmethod
    async def list_insurance_products(
        *,
        partner_code: str = DEFAULT_INSURANCE_PARTNER_CODE,
        actor_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise AutomotivePartnerIntegrationError(f"Insurance partner {partner_code} not found")
            products = await repo.list_products_for_partner(partner.id)
        return [AutomotivePartnerIntegrationEngineV1._product_snapshot(p) for p in products]

    @staticmethod
    async def get_insurance_product_detail(
        product_code: str,
        *,
        partner_code: str = DEFAULT_INSURANCE_PARTNER_CODE,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        tenant_id = None
        if actor_id is not None:
            tenant_id = await AutomotivePartnerIntegrationEngineV1._tenant_id_for_actor(actor_id)

        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise AutomotivePartnerIntegrationError(f"Insurance partner {partner_code} not found")
            product = await repo.get_product_by_code(partner.id, product_code)
            if product is None:
                raise AutomotivePartnerIntegrationError(f"Product {product_code} not found")
            offer = await repo.get_insurance_offer_for_product(product.id, tenant_id=tenant_id)

        payload = AutomotivePartnerIntegrationEngineV1._product_snapshot(product)
        payload["partner"] = AutomotivePartnerIntegrationEngineV1._partner_snapshot(partner)
        if offer:
            payload["offer"] = AutomotivePartnerIntegrationEngineV1._offer_snapshot(offer)
        return payload

    @staticmethod
    async def list_dealer_sources(
        *,
        actor_id: int | None = None,
        partner_code: str | None = None,
    ) -> list[dict[str, Any]]:
        tenant_id = None
        if actor_id is not None:
            tenant_id = await AutomotivePartnerIntegrationEngineV1._tenant_id_for_actor(actor_id)

        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            partner_id = None
            if partner_code:
                partner = await repo.get_partner_by_code(partner_code)
                if partner is None:
                    raise AutomotivePartnerIntegrationError(f"Dealer partner {partner_code} not found")
                partner_id = partner.id
            rows = await repo.list_dealer_sources(tenant_id=tenant_id, partner_id=partner_id)
        return [AutomotivePartnerIntegrationEngineV1._dealer_source_snapshot(r) for r in rows]

    @staticmethod
    async def get_dealer_partner(
        *,
        partner_code: str = DEFAULT_DEALER_PARTNER_CODE,
    ) -> dict[str, Any]:
        async with get_session() as session:
            partner = await AutomotivePartnerRepository(session).get_partner_by_code(partner_code)
        if partner is None:
            raise AutomotivePartnerIntegrationError(f"Dealer partner {partner_code} not found")
        if partner.partner_type != AutomotivePartnerType.DEALER.value:
            raise AutomotivePartnerIntegrationError(f"Partner {partner_code} is not a dealer")
        return AutomotivePartnerIntegrationEngineV1._partner_snapshot(partner)

    @staticmethod
    def format_insurance_menu_text(partner: dict[str, Any], products: list[dict[str, Any]]) -> str:
        lines = [
            "🛡 Insurance",
            "",
            f"Partner: {partner['name']}",
        ]
        if partner.get("website"):
            lines.append(f"Website: {partner['website']}")
        lines.append("")
        lines.append("Products:")
        for product in products:
            lines.append(f"• {product['name']}")
        lines.append("")
        lines.append("Select a product below for details.")
        return "\n".join(lines)

    @staticmethod
    def format_insurance_product_text(detail: dict[str, Any]) -> str:
        partner = detail.get("partner") or {}
        lines = [
            f"🛡 {detail['name']}",
            "",
            f"Partner: {partner.get('name', '—')}",
        ]
        if detail.get("description"):
            lines.append(detail["description"])
        offer = detail.get("offer")
        if offer:
            if offer.get("summary"):
                lines.append(f"\n{offer['summary']}")
            if offer.get("premium_from"):
                lines.append(f"From: {offer['premium_from']} {offer.get('currency', 'UAH')}")
            url = offer.get("external_url") or detail.get("external_url") or partner.get("website")
        else:
            url = detail.get("external_url") or partner.get("website")
        if url:
            lines.append(f"\n🔗 {url}")
        return "\n".join(lines)

    @staticmethod
    def format_dealer_sources_report(sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "No dealer sources configured."
        lines = ["📡 Dealer sources", ""]
        for source in sources:
            channel = source.get("channel_username") or source.get("channel_id") or "—"
            tenant = source.get("tenant_id") or "global"
            lines.append(
                f"• {source['source_code']} ({source['source_type']}) — {channel} [tenant: {tenant}]"
            )
        return "\n".join(lines)

    @staticmethod
    async def registry_health() -> dict[str, Any]:
        async with get_session() as session:
            repo = AutomotivePartnerRepository(session)
            insurance = await repo.get_partner_by_code(DEFAULT_INSURANCE_PARTNER_CODE)
            dealer = await repo.get_partner_by_code(DEFAULT_DEALER_PARTNER_CODE)
            product_count = 0
            source_count = 0
            if insurance:
                product_count = len(await repo.list_products_for_partner(insurance.id))
            if dealer:
                source_count = len(await repo.list_dealer_sources(partner_id=dealer.id))
        ok = insurance is not None and dealer is not None and product_count >= 5 and source_count >= 1
        return {
            "ok": ok,
            "insurance_partner": insurance.code if insurance else None,
            "dealer_partner": dealer.code if dealer else None,
            "insurance_products": product_count,
            "dealer_sources": source_count,
        }
