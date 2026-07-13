# BidEx Telegram Quote Parser v1 — @bidex_Odesa authoritative dealer rates.

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

from config import BIDEX_TELEGRAM_CHANNEL_ID, BIDEX_TELEGRAM_CHANNEL_USERNAME
from database.models.audit_log import AuditAction
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.automotive_treasury_repository import AutomotiveTreasuryRepository
from services.dealer_quote_constants import (
    BIDEX_RATES_TAG,
    BIDEX_SOURCE_AUTHORITY,
    SOURCE_AUTHORITY,
)
from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1

USD_UAH_PATTERN = re.compile(
    r"USD\s*/\s*UAH\s*:?\s*([\d]+(?:[.,]\d+)?)\s*/\s*([\d]+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
EUR_UAH_PATTERN = re.compile(
    r"EUR\s*/\s*UAH\s*:?\s*([\d]+(?:[.,]\d+)?)\s*/\s*([\d]+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
EUR_USD_PATTERN = re.compile(
    r"EUR\s*/\s*USD\s*:?\s*([\d]+(?:[.,]\d+)?)\s*/\s*([\d]+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
USDT_BUY_MARKUP_PATTERN = re.compile(
    r"(?:Купівля|Kupivlia|Buy)\s*:?\s*([+-]?[\d]+(?:[.,]\d+)?)\s*%",
    re.IGNORECASE,
)
USDT_SELL_MARKUP_PATTERN = re.compile(
    r"(?:Продаж|Prodazh|Sell)\s*:?\s*([+-]?[\d]+(?:[.,]\d+)?)\s*%",
    re.IGNORECASE,
)

_parser_health: dict[str, Any] = {
    "status": "unknown",
    "last_success_at": None,
    "last_error": None,
    "last_message_id": None,
    "last_channel_id": None,
    "quotes_active": False,
}

_configured_parser: "BidExTelegramQuoteParserV1 | None" = None


class QuoteAuthorityService(Protocol):
    @staticmethod
    async def refresh_reference_sources(*, sources: list[str] | None = None) -> dict[str, Any]: ...

    @staticmethod
    async def calculate_deviations(
        *,
        tenant_id: uuid.UUID | None = None,
        warning_pct: Decimal | None = None,
        critical_pct: Decimal | None = None,
    ) -> dict[str, Any]: ...


class BidExQuoteParserError(Exception):
    pass


class BidExTelegramQuoteParserV1:
    def __init__(self, authority_service: QuoteAuthorityService | None = None) -> None:
        self._authority_service = authority_service

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_decimal(raw: str) -> Decimal:
        return Decimal(raw.strip().replace(",", "."))

    @staticmethod
    def _has_exchange_rates(text: str) -> bool:
        return bool(
            USD_UAH_PATTERN.search(text)
            and EUR_UAH_PATTERN.search(text)
            and EUR_USD_PATTERN.search(text)
        )

    @staticmethod
    def should_parse(text: str) -> bool:
        if not text or not text.strip():
            return False
        if BIDEX_RATES_TAG not in text:
            return False
        return BidExTelegramQuoteParserV1._has_exchange_rates(text)

    @staticmethod
    def parse_message(text: str) -> dict[str, Decimal]:
        if not BidExTelegramQuoteParserV1.should_parse(text):
            raise BidExQuoteParserError("Message is not a BidEx rates update (#BIDEX_RATES required)")

        usd = USD_UAH_PATTERN.search(text)
        eur = EUR_UAH_PATTERN.search(text)
        eurusd = EUR_USD_PATTERN.search(text)
        if not usd or not eur or not eurusd:
            raise BidExQuoteParserError("Missing USD/UAH, EUR/UAH, or EUR/USD rates")

        usd_buy = BidExTelegramQuoteParserV1._parse_decimal(usd.group(1))
        usd_sell = BidExTelegramQuoteParserV1._parse_decimal(usd.group(2))
        eur_buy = BidExTelegramQuoteParserV1._parse_decimal(eur.group(1))
        eur_sell = BidExTelegramQuoteParserV1._parse_decimal(eur.group(2))
        eurusd_buy = BidExTelegramQuoteParserV1._parse_decimal(eurusd.group(1))
        eurusd_sell = BidExTelegramQuoteParserV1._parse_decimal(eurusd.group(2))

        buy_markup = Decimal("0")
        sell_markup = Decimal("0")
        buy_match = USDT_BUY_MARKUP_PATTERN.search(text)
        sell_match = USDT_SELL_MARKUP_PATTERN.search(text)
        if buy_match:
            buy_markup = BidExTelegramQuoteParserV1._parse_decimal(buy_match.group(1))
        if sell_match:
            sell_markup = BidExTelegramQuoteParserV1._parse_decimal(sell_match.group(1))

        usdt_buy = usd_buy * (Decimal("1") + buy_markup / Decimal("100"))
        usdt_sell = usd_sell * (Decimal("1") + sell_markup / Decimal("100"))

        return {
            "usd_buy": usd_buy,
            "usd_sell": usd_sell,
            "eur_buy": eur_buy,
            "eur_sell": eur_sell,
            "eurusd_buy": eurusd_buy,
            "eurusd_sell": eurusd_sell,
            "usdt_buy_markup_percent": buy_markup,
            "usdt_sell_markup_percent": sell_markup,
            "USD_BUY": usd_buy,
            "USD_SELL": usd_sell,
            "EUR_BUY": eur_buy,
            "EUR_SELL": eur_sell,
            "USDT_BUY": usdt_buy,
            "USDT_SELL": usdt_sell,
        }

    @staticmethod
    def is_bidex_channel(chat_id: int | str, username: str | None = None) -> bool:
        chat = str(chat_id).strip()
        if BIDEX_TELEGRAM_CHANNEL_ID:
            cfg = str(BIDEX_TELEGRAM_CHANNEL_ID).strip()
            if cfg.startswith("@"):
                return (username or "").lower() == cfg.lstrip("@").lower()
            return chat == cfg or chat == cfg.lstrip("-")
        if username:
            return username.lower() == BIDEX_TELEGRAM_CHANNEL_USERNAME.lower()
        return False

    @staticmethod
    def _update_health(
        *,
        status: str,
        error: str | None = None,
        message_id: int | None = None,
        channel_id: str | None = None,
        quotes_active: bool | None = None,
        success: bool = False,
    ) -> None:
        global _parser_health
        now = BidExTelegramQuoteParserV1._now().isoformat()
        if success:
            _parser_health["last_success_at"] = now
            _parser_health["last_error"] = None
        elif error:
            _parser_health["last_error"] = error
        if message_id is not None:
            _parser_health["last_message_id"] = message_id
        if channel_id is not None:
            _parser_health["last_channel_id"] = channel_id
        if quotes_active is not None:
            _parser_health["quotes_active"] = quotes_active
        _parser_health["status"] = status

    @staticmethod
    async def get_health_status(*, refresh_quotes: bool = True) -> dict[str, Any]:
        quotes_active = False
        last_sheet_at = None
        if refresh_quotes:
            try:
                sheet = await AutomotiveTreasuryEngineV1.get_active_rates()
                quotes_active = sheet.get("source_authority") == BIDEX_SOURCE_AUTHORITY
                last_sheet_at = sheet.get("source_updated_at")
            except Exception:
                quotes_active = False

        channel_configured = bool(BIDEX_TELEGRAM_CHANNEL_ID or BIDEX_TELEGRAM_CHANNEL_USERNAME)
        if not channel_configured:
            status = "unconfigured"
        elif quotes_active:
            status = "healthy"
        elif _parser_health.get("last_success_at"):
            status = "degraded"
        elif _parser_health.get("last_error"):
            status = "unhealthy"
        else:
            status = "waiting"

        payload = {
            "parser": "bidex_telegram_quote_parser_v1",
            "channel": f"@{BIDEX_TELEGRAM_CHANNEL_USERNAME}",
            "channel_configured": channel_configured,
            "quotes_active": quotes_active,
            "last_success_at": _parser_health.get("last_success_at"),
            "last_error": _parser_health.get("last_error"),
            "last_message_id": _parser_health.get("last_message_id"),
            "last_channel_id": _parser_health.get("last_channel_id"),
            "last_sheet_at": last_sheet_at,
            "tag_required": BIDEX_RATES_TAG,
        }
        BidExTelegramQuoteParserV1._update_health(status=status, quotes_active=quotes_active)
        return {"status": status, **payload}

    async def _ingest_channel_message(
        self,
        text: str,
        *,
        channel_id: str | int,
        message_id: int,
        tenant_id: uuid.UUID | None = None,
        updated_by_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        if not BidExTelegramQuoteParserV1.should_parse(text):
            return None

        try:
            parsed = BidExTelegramQuoteParserV1.parse_message(text)
        except BidExQuoteParserError as exc:
            BidExTelegramQuoteParserV1._update_health(
                status="unhealthy",
                error=str(exc),
                message_id=message_id,
                channel_id=str(channel_id),
            )
            raise

        now = BidExTelegramQuoteParserV1._now()

        async with get_session() as session:
            repo = AutomotiveTreasuryRepository(session)
            existing = await repo.get_active_sheet(tenant_id=tenant_id)
            if (
                existing is not None
                and message_id
                and existing.source_message_id is not None
                and message_id <= existing.source_message_id
                and existing.source_authority == BIDEX_SOURCE_AUTHORITY
            ):
                await session.refresh(existing)
                return AutomotiveTreasuryEngineV1._sheet_snapshot(existing)

            row = await repo.upsert_active_sheet(
                tenant_id=tenant_id,
                rates=parsed,
                source_updated_at=now,
                source_channel_id=str(channel_id),
                source_message_id=message_id,
                source_text=text,
                updated_by_user_id=updated_by_user_id,
                source_authority=BIDEX_SOURCE_AUTHORITY,
                eurusd_buy=parsed["eurusd_buy"],
                eurusd_sell=parsed["eurusd_sell"],
                usdt_buy_markup_percent=parsed["usdt_buy_markup_percent"],
                usdt_sell_markup_percent=parsed["usdt_sell_markup_percent"],
            )
            history_rates = {
                "usd_buy": str(parsed["usd_buy"]),
                "usd_sell": str(parsed["usd_sell"]),
                "eur_buy": str(parsed["eur_buy"]),
                "eur_sell": str(parsed["eur_sell"]),
                "eurusd_buy": str(parsed["eurusd_buy"]),
                "eurusd_sell": str(parsed["eurusd_sell"]),
                "usdt_buy_markup_percent": str(parsed["usdt_buy_markup_percent"]),
                "usdt_sell_markup_percent": str(parsed["usdt_sell_markup_percent"]),
                "USDT_BUY": str(parsed["USDT_BUY"]),
                "USDT_SELL": str(parsed["USDT_SELL"]),
                "source_authority": BIDEX_SOURCE_AUTHORITY,
            }
            await repo.record_history(
                tenant_id=tenant_id,
                rates=history_rates,
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
                    entity_type="bidex_quote_parser",
                    entity_id=str(row.id),
                    action=AuditAction.UPDATE.value,
                    new_value=history_rates,
                )
            await session.refresh(row)
            sheet = AutomotiveTreasuryEngineV1._sheet_snapshot(row)

        if self._authority_service is not None:
            try:
                await self._authority_service.refresh_reference_sources()
                await self._authority_service.calculate_deviations(tenant_id=tenant_id)
            except Exception:
                pass

        BidExTelegramQuoteParserV1._update_health(
            status="healthy",
            message_id=message_id,
            channel_id=str(channel_id),
            quotes_active=True,
            success=True,
        )
        sheet["authority"] = BIDEX_SOURCE_AUTHORITY
        return sheet

    @classmethod
    async def ingest_channel_message(
        cls,
        text: str,
        *,
        channel_id: str | int,
        message_id: int,
        tenant_id: uuid.UUID | None = None,
        updated_by_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        return await get_bidex_parser()._ingest_channel_message(
            text,
            channel_id=channel_id,
            message_id=message_id,
            tenant_id=tenant_id,
            updated_by_user_id=updated_by_user_id,
        )


def configure_bidex_parser(
    authority_service: QuoteAuthorityService | None = None,
) -> BidExTelegramQuoteParserV1:
    global _configured_parser
    _configured_parser = BidExTelegramQuoteParserV1(authority_service=authority_service)
    return _configured_parser


def get_bidex_parser() -> BidExTelegramQuoteParserV1:
    global _configured_parser
    if _configured_parser is None:
        _configured_parser = BidExTelegramQuoteParserV1()
    return _configured_parser
