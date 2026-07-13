# Automotive Treasury Engine v1 — dealer rates from Telegram, vehicle FX equivalents.

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from config import DEALER_RATES_TELEGRAM_CHANNEL_ID, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.automotive_treasury_engine import (
    AUTOMOTIVE_TREASURY_CURRENCIES,
    DEALER_RATE_FIELDS,
    DealerRateField,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.automotive_treasury_repository import AutomotiveTreasuryRepository
from services.tenant_context import TenantContextService

REQUIRED_RATE_FIELDS = frozenset({
    DealerRateField.USD_BUY.value,
    DealerRateField.USD_SELL.value,
    DealerRateField.EUR_BUY.value,
    DealerRateField.EUR_SELL.value,
    DealerRateField.USDT_BUY.value,
    DealerRateField.USDT_SELL.value,
})

OPTIONAL_RATE_FIELDS = frozenset({
    DealerRateField.USD_WHITE_PREMIUM.value,
    DealerRateField.USD_BLUE_PREMIUM.value,
})

RATE_LINE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (DealerRateField.USD_BUY.value, re.compile(r"usd[\s_:-]*buy[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.USD_SELL.value, re.compile(r"usd[\s_:-]*sell[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.EUR_BUY.value, re.compile(r"eur[\s_:-]*buy[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.EUR_SELL.value, re.compile(r"eur[\s_:-]*sell[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.USDT_BUY.value, re.compile(r"usdt[\s_:-]*buy[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.USDT_SELL.value, re.compile(r"usdt[\s_:-]*sell[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.USD_WHITE_PREMIUM.value, re.compile(r"(?:usd[\s_:-]*)?white[\s_:-]*premium[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
    (DealerRateField.USD_BLUE_PREMIUM.value, re.compile(r"(?:usd[\s_:-]*)?blue[\s_:-]*premium[^\d]*([\d]+(?:[.,]\d+)?)", re.I)),
]

EXPLICIT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (field, re.compile(rf"{field.replace('_', '[_\\s-]*')}[\s:=]+([\d]+(?:[.,]\d+)?)", re.I))
    for field in DEALER_RATE_FIELDS
]


class AutomotiveTreasuryEngineError(Exception):
    pass


class AutomotiveTreasuryEngineV1:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_decimal(raw: str) -> Decimal:
        cleaned = raw.strip().replace(",", ".")
        return Decimal(cleaned)

    @staticmethod
    def parse_dealer_rates(text: str) -> dict[str, Decimal]:
        if not text or not text.strip():
            raise AutomotiveTreasuryEngineError("Empty rate message")

        found: dict[str, Decimal] = {}
        for field, pattern in EXPLICIT_PATTERNS:
            match = pattern.search(text)
            if match:
                found[field] = AutomotiveTreasuryEngineV1._parse_decimal(match.group(1))

        for field, pattern in RATE_LINE_PATTERNS:
            if field in found:
                continue
            match = pattern.search(text)
            if match:
                found[field] = AutomotiveTreasuryEngineV1._parse_decimal(match.group(1))

        missing = REQUIRED_RATE_FIELDS - found.keys()
        if missing:
            raise AutomotiveTreasuryEngineError(
                f"Missing dealer rate fields: {', '.join(sorted(missing))}"
            )
        return found

    @staticmethod
    def _sheet_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "is_active": row.is_active,
            "USD_BUY": str(row.usd_buy),
            "USD_SELL": str(row.usd_sell),
            "EUR_BUY": str(row.eur_buy),
            "EUR_SELL": str(row.eur_sell),
            "USDT_BUY": str(row.usdt_buy),
            "USDT_SELL": str(row.usdt_sell),
            "USD_WHITE_PREMIUM": str(row.usd_white_premium) if row.usd_white_premium is not None else None,
            "USD_BLUE_PREMIUM": str(row.usd_blue_premium) if row.usd_blue_premium is not None else None,
            "source_channel_id": row.source_channel_id,
            "source_message_id": row.source_message_id,
            "source_updated_at": row.source_updated_at.isoformat(),
        }

    @staticmethod
    def _rates_from_sheet(row) -> dict[str, Decimal]:
        rates = {
            "USD_BUY": row.usd_buy,
            "USD_SELL": row.usd_sell,
            "EUR_BUY": row.eur_buy,
            "EUR_SELL": row.eur_sell,
            "USDT_BUY": row.usdt_buy,
            "USDT_SELL": row.usdt_sell,
        }
        if row.usd_white_premium is not None:
            rates["USD_WHITE_PREMIUM"] = row.usd_white_premium
        if row.usd_blue_premium is not None:
            rates["USD_BLUE_PREMIUM"] = row.usd_blue_premium
        return rates

    @staticmethod
    async def get_active_rates(
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await AutomotiveTreasuryRepository(session).get_active_sheet(tenant_id=tenant_id)
        if row is None:
            raise AutomotiveTreasuryEngineError(
                "Dealer rates not configured. Update rates in the Telegram dealer channel."
            )
        return AutomotiveTreasuryEngineV1._sheet_snapshot(row)

    @staticmethod
    async def ingest_from_telegram(
        text: str,
        *,
        channel_id: str | int,
        message_id: int,
        tenant_id: uuid.UUID | None = None,
        updated_by_user_id: int | None = None,
    ) -> dict[str, Any]:
        rates = AutomotiveTreasuryEngineV1.parse_dealer_rates(text)
        now = AutomotiveTreasuryEngineV1._now()
        rates_payload = {key: str(value) for key, value in rates.items()}

        async with get_session() as session:
            repo = AutomotiveTreasuryRepository(session)
            row = await repo.upsert_active_sheet(
                tenant_id=tenant_id,
                rates=rates,
                source_updated_at=now,
                source_channel_id=str(channel_id),
                source_message_id=message_id,
                source_text=text,
                updated_by_user_id=updated_by_user_id,
            )
            await repo.record_history(
                tenant_id=tenant_id,
                rates=rates_payload,
                source_updated_at=now,
                source_channel_id=str(channel_id),
                source_message_id=message_id,
                source_text=text,
                updated_by_user_id=updated_by_user_id,
            )
            if updated_by_user_id:
                await AuditRepository(session).create_log(
                    user_id=updated_by_user_id,
                    tenant_id=tenant_id,
                    entity_type="automotive_treasury",
                    entity_id=str(row.id),
                    action=AuditAction.UPDATE.value,
                    new_value=rates_payload,
                )
            await session.refresh(row)
            return AutomotiveTreasuryEngineV1._sheet_snapshot(row)

    @staticmethod
    def is_dealer_rates_channel(chat_id: int | str) -> bool:
        if not DEALER_RATES_TELEGRAM_CHANNEL_ID:
            return False
        configured = str(DEALER_RATES_TELEGRAM_CHANNEL_ID).strip()
        chat = str(chat_id).strip()
        if configured.startswith("@"):
            return False
        return chat == configured or chat == configured.lstrip("-")

    @staticmethod
    def _mid(buy: Decimal, sell: Decimal) -> Decimal:
        return (buy + sell) / Decimal("2")

    @staticmethod
    def _to_uah(amount: Decimal, currency: str, rates: dict[str, Decimal]) -> Decimal:
        cur = currency.upper()
        if cur == "UAH":
            return amount
        if cur == "USD":
            return amount * rates["USD_SELL"]
        if cur == "EUR":
            return amount * rates["EUR_SELL"]
        if cur == "USDT":
            return amount * rates["USDT_SELL"]
        raise AutomotiveTreasuryEngineError(f"Unsupported currency: {currency}")

    @staticmethod
    def calculate_equivalents(
        amount: Decimal | str | float | int,
        *,
        currency: str = "UAH",
        rates: dict[str, Decimal] | None = None,
    ) -> dict[str, str]:
        if rates is None:
            raise AutomotiveTreasuryEngineError("Dealer rates required")
        try:
            value = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise AutomotiveTreasuryEngineError(f"Invalid amount: {amount}") from exc

        uah = AutomotiveTreasuryEngineV1._to_uah(value, currency, rates)
        usd_rate = AutomotiveTreasuryEngineV1._mid(rates["USD_BUY"], rates["USD_SELL"])
        eur_rate = AutomotiveTreasuryEngineV1._mid(rates["EUR_BUY"], rates["EUR_SELL"])
        usdt_rate = AutomotiveTreasuryEngineV1._mid(rates["USDT_BUY"], rates["USDT_SELL"])

        if usd_rate <= 0 or eur_rate <= 0 or usdt_rate <= 0:
            raise AutomotiveTreasuryEngineError("Invalid dealer rate values")

        return {
            "UAH": f"{uah.quantize(Decimal('0.01'))}",
            "USD": f"{(uah / usd_rate).quantize(Decimal('0.01'))}",
            "EUR": f"{(uah / eur_rate).quantize(Decimal('0.01'))}",
            "USDT": f"{(uah / usdt_rate).quantize(Decimal('0.01'))}",
        }

    @staticmethod
    async def calculate_listing_equivalents(
        *,
        amount: Decimal | str | float | int | None,
        currency: str = "UAH",
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, str] | None:
        if amount is None:
            return None
        async with get_session() as session:
            row = await AutomotiveTreasuryRepository(session).get_active_sheet(tenant_id=tenant_id)
        if row is None:
            raise AutomotiveTreasuryEngineError(
                "Dealer rates not configured. Update rates in the Telegram dealer channel."
            )
        rates = AutomotiveTreasuryEngineV1._rates_from_sheet(row)
        return AutomotiveTreasuryEngineV1.calculate_equivalents(
            amount,
            currency=currency,
            rates=rates,
        )

    @staticmethod
    async def enrich_vehicle_listing(
        listing: dict[str, Any],
        *,
        tenant_id: uuid.UUID | None = None,
        price_field: str = "sale_price",
        fallback_field: str = "total_cost",
    ) -> dict[str, Any]:
        amount = listing.get(price_field) or listing.get(fallback_field) or listing.get("target_price")
        if amount is None:
            listing["price_equivalents"] = None
            listing["rates_source"] = "dealer_telegram"
            return listing
        currency = (listing.get("currency") or "UAH").upper()
        if currency not in AUTOMOTIVE_TREASURY_CURRENCIES:
            currency = "UAH"
        listing["price_equivalents"] = await AutomotiveTreasuryEngineV1.calculate_listing_equivalents(
            amount=amount,
            currency=currency,
            tenant_id=tenant_id,
        )
        listing["rates_source"] = "dealer_telegram"
        return listing

    @staticmethod
    async def enrich_car_listing(
        car: dict[str, Any],
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        amount = car.get("sale_price") or car.get("total_cost") or car.get("purchase_price")
        if amount is None:
            car["price_equivalents"] = None
            car["rates_source"] = "dealer_telegram"
            return car
        car["price_equivalents"] = await AutomotiveTreasuryEngineV1.calculate_listing_equivalents(
            amount=amount,
            currency="UAH",
            tenant_id=tenant_id,
        )
        car["rates_source"] = "dealer_telegram"
        return car

    @staticmethod
    async def enrich_cars_for_actor(actor_id: int, cars: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tenant_id = None
        try:
            tenant_id = await TenantContextService.require_tenant_id(actor_id)
        except Exception:
            tenant_id = None
        enriched: list[dict[str, Any]] = []
        for car in cars:
            try:
                enriched.append(
                    await AutomotiveTreasuryEngineV1.enrich_car_listing(
                        dict(car),
                        tenant_id=tenant_id,
                    )
                )
            except AutomotiveTreasuryEngineError:
                item = dict(car)
                item["price_equivalents"] = None
                item["rates_error"] = "dealer_rates_unavailable"
                item["rates_source"] = "dealer_telegram"
                enriched.append(item)
        return enriched

    @staticmethod
    def format_rates_report(sheet: dict[str, Any]) -> str:
        lines = [
            "💱 Dealer Rates (Telegram)",
            "",
            f"USD: buy {sheet['USD_BUY']} / sell {sheet['USD_SELL']}",
            f"EUR: buy {sheet['EUR_BUY']} / sell {sheet['EUR_SELL']}",
            f"USDT: buy {sheet['USDT_BUY']} / sell {sheet['USDT_SELL']}",
        ]
        if sheet.get("USD_WHITE_PREMIUM"):
            lines.append(f"USD white premium: {sheet['USD_WHITE_PREMIUM']}")
        if sheet.get("USD_BLUE_PREMIUM"):
            lines.append(f"USD blue premium: {sheet['USD_BLUE_PREMIUM']}")
        lines.append(f"\nUpdated: {sheet.get('source_updated_at', '—')}")
        lines.append("Source: Telegram dealer channel (no bank/exchange fallback)")
        return "\n".join(lines)

    @staticmethod
    async def get_rates_report(*, tenant_id: uuid.UUID | None = None) -> str:
        sheet = await AutomotiveTreasuryEngineV1.get_active_rates(tenant_id=tenant_id)
        return AutomotiveTreasuryEngineV1.format_rates_report(sheet)

    @staticmethod
    async def manual_upsert_for_owner(
        actor_id: int,
        text: str,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if actor_id != OWNER_ID:
            raise AutomotiveTreasuryEngineError("Owner only")
        return await AutomotiveTreasuryEngineV1.ingest_from_telegram(
            text,
            channel_id=DEALER_RATES_TELEGRAM_CHANNEL_ID or "manual",
            message_id=0,
            tenant_id=tenant_id,
            updated_by_user_id=actor_id,
        )
