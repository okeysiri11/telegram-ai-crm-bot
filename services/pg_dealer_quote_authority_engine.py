# Dealer Quote Authority Engine v1 — Foma Rates authority, reference deviation, alerts.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import aiohttp

from config import FOMA_RATES_TELEGRAM_CHANNEL_ID
from services.bidex_telegram_quote_parser import SOURCE_AUTHORITY as BIDEX_SOURCE_AUTHORITY, OWNER_ID
from database.models.dealer_quote_authority_engine import (
    AlertSeverity,
    QuotePair,
    ReferenceSourceCode,
)
from database.session import get_session
from repositories.dealer_quote_authority_repository import (
    MarketAlertRepository,
    QuoteDeviationRepository,
    ReferenceMarketQuoteRepository,
)
from services.market_reference_connectors import REFERENCE_FETCHERS, ReferenceConnectorError
from services.pg_automotive_treasury_engine import (
    AutomotiveTreasuryEngineError,
    AutomotiveTreasuryEngineV1,
)

DEFAULT_DEVIATION_WARNING_PCT = Decimal("1.5")
DEFAULT_DEVIATION_CRITICAL_PCT = Decimal("3.0")

PAIR_DEALER_FIELDS = {
    QuotePair.USD_UAH.value: ("USD_BUY", "USD_SELL"),
    QuotePair.EUR_UAH.value: ("EUR_BUY", "EUR_SELL"),
    QuotePair.USDT_UAH.value: ("USDT_BUY", "USDT_SELL"),
}


class DealerQuoteAuthorityEngineError(Exception):
    pass


class DealerQuoteAuthorityEngineV1:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def is_foma_rates_channel(chat_id: int | str) -> bool:
        if FOMA_RATES_TELEGRAM_CHANNEL_ID:
            return str(chat_id).strip() == str(FOMA_RATES_TELEGRAM_CHANNEL_ID).strip()
        return AutomotiveTreasuryEngineV1.is_dealer_rates_channel(chat_id)

    @staticmethod
    async def get_authoritative_quotes(
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        sheet = await AutomotiveTreasuryEngineV1.get_active_rates(tenant_id=tenant_id)
        authority = sheet.get("source_authority") or BIDEX_SOURCE_AUTHORITY
        sheet["authority"] = authority
        sheet["expires"] = False
        return sheet

    @staticmethod
    async def ingest_foma_rates(
        text: str,
        *,
        channel_id: str | int,
        message_id: int,
        tenant_id: uuid.UUID | None = None,
        updated_by_user_id: int | None = None,
    ) -> dict[str, Any]:
        sheet = await AutomotiveTreasuryEngineV1.ingest_from_telegram(
            text,
            channel_id=channel_id,
            message_id=message_id,
            tenant_id=tenant_id,
            updated_by_user_id=updated_by_user_id,
        )
        await DealerQuoteAuthorityEngineV1.refresh_reference_sources()
        await DealerQuoteAuthorityEngineV1.calculate_deviations(tenant_id=tenant_id)
        sheet["authority"] = "foma_rates_telegram"
        return sheet

    @staticmethod
    async def refresh_reference_sources(
        *,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        target = sources or list(REFERENCE_FETCHERS.keys())
        captured_at = DealerQuoteAuthorityEngineV1._now()
        stored: list[dict[str, Any]] = []
        failed: list[str] = []

        async with get_session() as session:
            repo = ReferenceMarketQuoteRepository(session)
            async with aiohttp.ClientSession() as http:
                for source_code in target:
                    fetcher = REFERENCE_FETCHERS.get(source_code)
                    if fetcher is None:
                        failed.append(source_code)
                        continue
                    try:
                        config = await DealerQuoteAuthorityEngineV1._source_config(source_code)
                        quotes = await fetcher(http, config)
                        for pair, values in quotes.items():
                            row = await repo.create(
                                source_code=source_code,
                                pair=pair,
                                bid=values["bid"],
                                ask=values["ask"],
                                mid=values["mid"],
                                captured_at=captured_at,
                                payload={"reference_only": True},
                            )
                            stored.append(
                                {
                                    "source": source_code,
                                    "pair": pair,
                                    "mid": str(row.mid),
                                }
                            )
                    except (ReferenceConnectorError, aiohttp.ClientError, Exception):
                        failed.append(source_code)

        return {
            "stored": len(stored),
            "failed": failed,
            "quotes": stored[:30],
            "captured_at": captured_at.isoformat(),
        }

    @staticmethod
    async def _source_config(source_code: str) -> dict[str, Any]:
        from database.models.market_data import MarketSourceCode
        from repositories.market_data_repository import MarketSourceRepository

        async with get_session() as session:
            source = await MarketSourceRepository(session).get_by_code(source_code)
            if source and source.config:
                return source.config
        defaults = {
            ReferenceSourceCode.TRADINGVIEW.value: {
                "fallback_rates": {
                    QuotePair.USD_UAH.value: {"bid": "41.0", "ask": "41.5"},
                    QuotePair.EUR_UAH.value: {"bid": "44.0", "ask": "44.8"},
                    QuotePair.USDT_UAH.value: {"bid": "41.0", "ask": "41.4"},
                }
            },
        }
        return defaults.get(source_code, {})

    @staticmethod
    def _dealer_mid(sheet: dict[str, Any], pair: str) -> Decimal:
        buy_key, sell_key = PAIR_DEALER_FIELDS[pair]
        buy = Decimal(str(sheet[buy_key]))
        sell = Decimal(str(sheet[sell_key]))
        return (buy + sell) / Decimal("2")

    @staticmethod
    async def calculate_deviations(
        *,
        tenant_id: uuid.UUID | None = None,
        warning_pct: Decimal = DEFAULT_DEVIATION_WARNING_PCT,
        critical_pct: Decimal = DEFAULT_DEVIATION_CRITICAL_PCT,
    ) -> dict[str, Any]:
        try:
            sheet = await DealerQuoteAuthorityEngineV1.get_authoritative_quotes(tenant_id=tenant_id)
        except AutomotiveTreasuryEngineError as exc:
            raise DealerQuoteAuthorityEngineError(str(exc)) from exc

        sheet_id = uuid.UUID(sheet["id"]) if sheet.get("id") else None
        now = DealerQuoteAuthorityEngineV1._now()
        deviations: list[dict[str, Any]] = []
        alerts_created = 0

        async with get_session() as session:
            ref_repo = ReferenceMarketQuoteRepository(session)
            dev_repo = QuoteDeviationRepository(session)
            alert_repo = MarketAlertRepository(session)
            await alert_repo.resolve_stale(resolved_at=now)

            for pair in PAIR_DEALER_FIELDS:
                dealer_mid = DealerQuoteAuthorityEngineV1._dealer_mid(sheet, pair)
                for source_code in REFERENCE_FETCHERS:
                    ref = await ref_repo.latest_by_source_pair(source_code, pair)
                    if ref is None:
                        continue
                    deviation_abs = dealer_mid - ref.mid
                    deviation_pct = (
                        (deviation_abs / ref.mid * Decimal("100"))
                        if ref.mid > 0
                        else Decimal("0")
                    )
                    await dev_repo.create(
                        pair=pair,
                        source_code=source_code,
                        dealer_mid=dealer_mid,
                        reference_mid=ref.mid,
                        deviation_abs=deviation_abs,
                        deviation_pct=deviation_pct,
                        calculated_at=now,
                        dealer_sheet_id=sheet_id,
                    )
                    item = {
                        "pair": pair,
                        "source": source_code,
                        "dealer_mid": str(dealer_mid),
                        "reference_mid": str(ref.mid),
                        "deviation_pct": str(deviation_pct.quantize(Decimal("0.01"))),
                    }
                    deviations.append(item)

                    abs_pct = abs(deviation_pct)
                    if abs_pct >= critical_pct:
                        severity = AlertSeverity.CRITICAL.value
                    elif abs_pct >= warning_pct:
                        severity = AlertSeverity.WARNING.value
                    else:
                        continue
                    await alert_repo.create(
                        alert_type="abnormal_deviation",
                        severity=severity,
                        pair=pair,
                        source_code=source_code,
                        message=(
                            f"{pair} dealer vs {source_code}: "
                            f"{deviation_pct.quantize(Decimal('0.01'))}% deviation"
                        ),
                        deviation_pct=deviation_pct,
                        payload=item,
                    )
                    alerts_created += 1

        return {
            "deviations": deviations,
            "alerts_created": alerts_created,
            "calculated_at": now.isoformat(),
        }

    @staticmethod
    async def get_treasury_dashboard(
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        sheet = await DealerQuoteAuthorityEngineV1.get_authoritative_quotes(tenant_id=tenant_id)
        spread_analysis = {}
        for pair, (buy_key, sell_key) in PAIR_DEALER_FIELDS.items():
            buy = Decimal(str(sheet[buy_key]))
            sell = Decimal(str(sheet[sell_key]))
            spread_abs = sell - buy
            mid = (buy + sell) / Decimal("2")
            spread_pct = (spread_abs / mid * Decimal("100")) if mid > 0 else Decimal("0")
            spread_analysis[pair] = {
                "buy": str(buy),
                "sell": str(sell),
                "spread_abs": str(spread_abs.quantize(Decimal("0.0001"))),
                "spread_pct": str(spread_pct.quantize(Decimal("0.01"))),
            }

        async with get_session() as session:
            alerts = await MarketAlertRepository(session).list_unresolved(limit=10)
            latest_devs = []
            for pair in PAIR_DEALER_FIELDS:
                rows = await QuoteDeviationRepository(session).latest_for_pair(pair, limit=5)
                for row in rows:
                    latest_devs.append(
                        {
                            "pair": row.pair,
                            "source": row.source_code,
                            "deviation_pct": str(row.deviation_pct),
                        }
                    )

        return {
            "authority": "foma_rates_telegram",
            "dealer_quotes": sheet,
            "spread_analysis": spread_analysis,
            "recent_deviations": latest_devs[:20],
            "active_alerts": [
                {
                    "severity": a.severity,
                    "pair": a.pair,
                    "source": a.source_code,
                    "message": a.message,
                }
                for a in alerts
            ],
        }

    @staticmethod
    def format_treasury_dashboard(dashboard: dict[str, Any]) -> str:
        lines = [
            "🏦 Treasury Dashboard",
            "",
            "Authority: @bidex_Odesa (Telegram)",
            "Quotes do not expire automatically.",
            "",
            "Dealer spreads:",
        ]
        for pair, spread in (dashboard.get("spread_analysis") or {}).items():
            lines.append(
                f"• {pair}: buy {spread['buy']} / sell {spread['sell']} "
                f"(spread {spread['spread_pct']}%)"
            )
        devs = dashboard.get("recent_deviations") or []
        if devs:
            lines.append("")
            lines.append("Market deviation (reference-only):")
            for item in devs[:8]:
                lines.append(
                    f"• {item['pair']} vs {item['source']}: {item['deviation_pct']}%"
                )
        alerts = dashboard.get("active_alerts") or []
        if alerts:
            lines.append("")
            lines.append(f"Active alerts: {len(alerts)}")
            for alert in alerts[:5]:
                lines.append(f"• [{alert['severity']}] {alert['message']}")
        lines.append("")
        lines.append("External sources are reference-only — not used for business calculations.")
        return "\n".join(lines)

    @staticmethod
    async def calculate_business_equivalents(
        amount: Decimal | str | float | int,
        *,
        currency: str = "UAH",
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, str]:
        await DealerQuoteAuthorityEngineV1.get_authoritative_quotes(tenant_id=tenant_id)
        return await AutomotiveTreasuryEngineV1.calculate_listing_equivalents(
            amount=amount,
            currency=currency,
            tenant_id=tenant_id,
        )
