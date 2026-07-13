# Dealer Quote Authority Engine v1 tests.

from __future__ import annotations

from decimal import Decimal

from database.models.dealer_quote_authority_engine import QuotePair
from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1
from services.pg_dealer_quote_authority_engine import (
    DEFAULT_DEVIATION_CRITICAL_PCT,
    DEFAULT_DEVIATION_WARNING_PCT,
    DealerQuoteAuthorityEngineV1,
    PAIR_DEALER_FIELDS,
)


SAMPLE_RATE_TEXT = """
Foma Rates
USD buy: 41.20 sell: 41.80
EUR buy: 44.50 sell: 45.10
USDT buy: 41.10 sell: 41.70
"""


def run_pair_fields_test() -> dict:
    checks = {
        "usd_pair": QuotePair.USD_UAH.value in PAIR_DEALER_FIELDS,
        "eur_pair": QuotePair.EUR_UAH.value in PAIR_DEALER_FIELDS,
        "usdt_pair": QuotePair.USDT_UAH.value in PAIR_DEALER_FIELDS,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_dealer_mid_test() -> dict:
    rates = AutomotiveTreasuryEngineV1.parse_dealer_rates(SAMPLE_RATE_TEXT)
    sheet = {key: str(value) for key, value in rates.items()}
    mid = DealerQuoteAuthorityEngineV1._dealer_mid(sheet, "USD_UAH")
    expected = (Decimal("41.20") + Decimal("41.80")) / Decimal("2")
    checks = {"mid_matches": mid == expected}
    return {"ok": all(checks.values()), "checks": checks, "mid": str(mid)}


def run_dashboard_format_test() -> dict:
    dashboard = {
        "spread_analysis": {
            "USD_UAH": {
                "buy": "41.20",
                "sell": "41.80",
                "spread_pct": "1.44",
            }
        },
        "recent_deviations": [
            {"pair": "USD_UAH", "source": "OKX", "deviation_pct": "0.50"},
        ],
        "active_alerts": [],
    }
    text = DealerQuoteAuthorityEngineV1.format_treasury_dashboard(dashboard)
    checks = {
        "has_title": "Treasury Dashboard" in text,
        "has_spread": "USD_UAH" in text,
        "has_reference_note": "reference-only" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_deviation_thresholds_test() -> dict:
    checks = {
        "warning_positive": DEFAULT_DEVIATION_WARNING_PCT > Decimal("0"),
        "critical_gt_warning": DEFAULT_DEVIATION_CRITICAL_PCT > DEFAULT_DEVIATION_WARNING_PCT,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_dealer_rate_service_import_test() -> dict:
    from services.dealer_rate_service import DealerRateService

    checks = {
        "has_get_rates": hasattr(DealerRateService, "get_authoritative_rates"),
        "has_otc_mid": hasattr(DealerRateService, "get_otc_usdt_mid"),
        "has_enrich": hasattr(DealerRateService, "enrich_car_listings"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_dealer_quote_authority_test_suite() -> dict:
    pair_fields = run_pair_fields_test()
    dealer_mid = run_dealer_mid_test()
    dashboard = run_dashboard_format_test()
    thresholds = run_deviation_thresholds_test()
    service = run_dealer_rate_service_import_test()
    ok = all(
        item.get("ok")
        for item in (pair_fields, dealer_mid, dashboard, thresholds, service)
    )
    return {
        "ok": ok,
        "pair_fields": pair_fields,
        "dealer_mid": dealer_mid,
        "dashboard": dashboard,
        "thresholds": thresholds,
        "service": service,
        "quote_pair_enum": QuotePair.USD_UAH.value,
    }


def run_dealer_quote_authority_tests() -> dict:
    return run_dealer_quote_authority_test_suite()
