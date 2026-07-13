# Automotive Treasury Engine v1 tests.

from __future__ import annotations

from decimal import Decimal

from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1


SAMPLE_RATE_TEXT = """
Dealer rates update
USD buy: 41.20 sell: 41.80
EUR buy: 44.50 sell: 45.10
USDT buy: 41.10 sell: 41.70
USD white premium: 0.35
USD blue premium: 0.90
"""


def run_rate_parser_test() -> dict:
    rates = AutomotiveTreasuryEngineV1.parse_dealer_rates(SAMPLE_RATE_TEXT)
    checks = {
        "usd_buy": rates["USD_BUY"] == Decimal("41.20"),
        "usd_sell": rates["USD_SELL"] == Decimal("41.80"),
        "eur_buy": rates["EUR_BUY"] == Decimal("44.50"),
        "usdt_sell": rates["USDT_SELL"] == Decimal("41.70"),
        "white_premium": rates.get("USD_WHITE_PREMIUM") == Decimal("0.35"),
        "blue_premium": rates.get("USD_BLUE_PREMIUM") == Decimal("0.90"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_equivalents_test() -> dict:
    rates = AutomotiveTreasuryEngineV1.parse_dealer_rates(SAMPLE_RATE_TEXT)
    eq = AutomotiveTreasuryEngineV1.calculate_equivalents(
        Decimal("418000"),
        currency="UAH",
        rates=rates,
    )
    checks = {
        "has_uah": "UAH" in eq,
        "has_usd": "USD" in eq,
        "has_eur": "EUR" in eq,
        "has_usdt": "USDT" in eq,
        "uah_matches": eq["UAH"] == "418000.00",
    }
    return {"ok": all(checks.values()), "checks": checks, "equivalents": eq}


def run_no_fallback_test() -> dict:
    try:
        AutomotiveTreasuryEngineV1.calculate_equivalents(
            Decimal("1000"),
            currency="UAH",
            rates=None,
        )
        return {"ok": False, "checks": {"raised": False}}
    except Exception:
        return {"ok": True, "checks": {"raised": True}}


def run_automotive_treasury_test_suite() -> dict:
    parser = run_rate_parser_test()
    equivalents = run_equivalents_test()
    no_fallback = run_no_fallback_test()
    ok = parser.get("ok") and equivalents.get("ok") and no_fallback.get("ok")
    return {
        "ok": ok,
        "parser": parser,
        "equivalents": equivalents,
        "no_fallback": no_fallback,
    }


def run_automotive_treasury_tests() -> dict:
    return run_automotive_treasury_test_suite()
