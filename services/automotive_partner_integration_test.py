# Automotive Partner Integration v1 tests.

from __future__ import annotations

from services.pg_automotive_partner_integration_engine import (
    DEFAULT_DEALER_PARTNER_CODE,
    DEFAULT_INSURANCE_PARTNER_CODE,
    AutomotivePartnerIntegrationEngineV1,
)


SAMPLE_PRODUCTS = [
    {"product_code": "OSAGO", "name": "OSAGO"},
    {"product_code": "CASCO", "name": "CASCO"},
]


def run_partner_codes_test() -> dict:
    checks = {
        "insurance_code": DEFAULT_INSURANCE_PARTNER_CODE == "sgtas",
        "dealer_code": DEFAULT_DEALER_PARTNER_CODE == "boroda_cars",
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_insurance_menu_format_test() -> dict:
    partner = {
        "name": "SG TAS",
        "website": "https://sgtas.ua",
    }
    text = AutomotivePartnerIntegrationEngineV1.format_insurance_menu_text(partner, SAMPLE_PRODUCTS)
    checks = {
        "has_partner": "SG TAS" in text,
        "has_website": "sgtas.ua" in text,
        "has_osago": "OSAGO" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_insurance_product_format_test() -> dict:
    detail = {
        "name": "Green Card",
        "description": "International motor insurance",
        "partner": {"name": "SG TAS", "website": "https://sgtas.ua"},
        "offer": {
            "summary": "Coverage abroad",
            "premium_from": "500",
            "currency": "UAH",
            "external_url": "https://sgtas.ua",
        },
    }
    text = AutomotivePartnerIntegrationEngineV1.format_insurance_product_text(detail)
    checks = {
        "has_product": "Green Card" in text,
        "has_url": "sgtas.ua" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_dealer_source_format_test() -> dict:
    sources = [
        {
            "source_code": "boroda_cars_telegram",
            "source_type": "telegram_channel",
            "channel_username": "boroda_cars",
            "tenant_id": None,
        }
    ]
    text = AutomotivePartnerIntegrationEngineV1.format_dealer_sources_report(sources)
    checks = {
        "has_channel": "boroda_cars" in text,
        "has_type": "telegram_channel" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_automotive_partner_integration_test_suite() -> dict:
    codes = run_partner_codes_test()
    menu = run_insurance_menu_format_test()
    product = run_insurance_product_format_test()
    dealer = run_dealer_source_format_test()
    ok = all(item.get("ok") for item in (codes, menu, product, dealer))
    return {
        "ok": ok,
        "codes": codes,
        "menu": menu,
        "product": product,
        "dealer": dealer,
    }


def run_automotive_partner_integration_tests() -> dict:
    return run_automotive_partner_integration_test_suite()
