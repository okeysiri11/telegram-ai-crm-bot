# Dealer Rate Service — single authoritative pricing entry for Automotive and OTC.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1
from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1


class DealerRateService:
    """All business calculations must use dealer quotes from @bidex_Odesa only."""

    @staticmethod
    async def get_authoritative_rates(
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        return await DealerQuoteAuthorityEngineV1.get_authoritative_quotes(tenant_id=tenant_id)

    @staticmethod
    async def convert(
        amount: Decimal | str | float | int,
        *,
        currency: str = "UAH",
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, str]:
        return await DealerQuoteAuthorityEngineV1.calculate_business_equivalents(
            amount,
            currency=currency,
            tenant_id=tenant_id,
        )

    @staticmethod
    async def enrich_car_listings(
        actor_id: int,
        cars: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return await AutomotiveTreasuryEngineV1.enrich_cars_for_actor(actor_id, cars)

    @staticmethod
    async def get_otc_usdt_mid(*, tenant_id: uuid.UUID | None = None) -> Decimal:
        rates = await DealerRateService.get_authoritative_rates(tenant_id=tenant_id)
        buy = Decimal(str(rates["USDT_BUY"]))
        sell = Decimal(str(rates["USDT_SELL"]))
        return (buy + sell) / Decimal("2")
