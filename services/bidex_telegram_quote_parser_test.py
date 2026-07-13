# BidEx Telegram Quote Parser v1 tests.

from __future__ import annotations

from decimal import Decimal

from services.bidex_telegram_quote_parser import (
    BIDEX_RATES_TAG,
    BidExQuoteParserError,
    BidExTelegramQuoteParserV1,
)

SAMPLE_BIDEX_MESSAGE = """
#BIDEX_RATES
Оновлення курсів

USD/UAH: 41.20 / 41.80
EUR/UAH: 44.50 / 45.10
EUR/USD: 1.078 / 1.085

USDT
Купівля: +0.5%
Продаж: -0.3%
"""

NO_TAG_MESSAGE = """
USD/UAH: 41.20 / 41.80
EUR/UAH: 44.50 / 45.10
EUR/USD: 1.078 / 1.085
"""


def run_should_parse_test() -> dict:
    checks = {
        "sample_ok": BidExTelegramQuoteParserV1.should_parse(SAMPLE_BIDEX_MESSAGE),
        "no_tag_rejected": not BidExTelegramQuoteParserV1.should_parse(NO_TAG_MESSAGE),
        "empty_rejected": not BidExTelegramQuoteParserV1.should_parse(""),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_parse_fields_test() -> dict:
    parsed = BidExTelegramQuoteParserV1.parse_message(SAMPLE_BIDEX_MESSAGE)
    checks = {
        "usd_buy": parsed["usd_buy"] == Decimal("41.20"),
        "usd_sell": parsed["usd_sell"] == Decimal("41.80"),
        "eur_buy": parsed["eur_buy"] == Decimal("44.50"),
        "eur_sell": parsed["eur_sell"] == Decimal("45.10"),
        "eurusd_buy": parsed["eurusd_buy"] == Decimal("1.078"),
        "eurusd_sell": parsed["eurusd_sell"] == Decimal("1.085"),
        "buy_markup": parsed["usdt_buy_markup_percent"] == Decimal("0.5"),
        "sell_markup": parsed["usdt_sell_markup_percent"] == Decimal("-0.3"),
    }
    expected_usdt_buy = Decimal("41.20") * Decimal("1.005")
    expected_usdt_sell = Decimal("41.80") * Decimal("0.997")
    checks["usdt_buy"] = parsed["USDT_BUY"] == expected_usdt_buy
    checks["usdt_sell"] = parsed["USDT_SELL"] == expected_usdt_sell
    return {"ok": all(checks.values()), "checks": checks, "parsed": {k: str(v) for k, v in parsed.items()}}


def run_ignore_invalid_test() -> dict:
    try:
        BidExTelegramQuoteParserV1.parse_message("hello world")
        return {"ok": False, "checks": {"raised": False}}
    except BidExQuoteParserError:
        return {"ok": True, "checks": {"raised": True}}


def run_channel_match_test() -> dict:
    checks = {
        "username_match": BidExTelegramQuoteParserV1.is_bidex_channel("-100123", "bidex_Odesa"),
        "wrong_username": not BidExTelegramQuoteParserV1.is_bidex_channel("-100123", "other"),
        "tag_constant": BIDEX_RATES_TAG == "#BIDEX_RATES",
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_bidex_quote_parser_test_suite() -> dict:
    should_parse = run_should_parse_test()
    parse_fields = run_parse_fields_test()
    ignore_invalid = run_ignore_invalid_test()
    channel_match = run_channel_match_test()
    ok = all(item.get("ok") for item in (should_parse, parse_fields, ignore_invalid, channel_match))
    return {
        "ok": ok,
        "should_parse": should_parse,
        "parse_fields": parse_fields,
        "ignore_invalid": ignore_invalid,
        "channel_match": channel_match,
    }


def run_bidex_quote_parser_tests() -> dict:
    return run_bidex_quote_parser_test_suite()
