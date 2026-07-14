# Automotive Partner Branding UI v1 tests.

from __future__ import annotations

from database.models.automotive_partner_integration import AutomotivePartnerType
from services.pg_automotive_partner_branding_engine import AutomotivePartnerBrandingEngineV1


SAMPLE_CARD = {
    "code": "sgtas",
    "name": "SG TAS",
    "website": "https://sgtas.ua",
    "branding": {
        "card_title": "SG TAS",
        "short_description": "Insurance leader in Ukraine.",
        "logo_emoji": "🛡",
        "logo_enabled": True,
        "logo_url": "https://sgtas.ua/logo.svg",
    },
    "ctas": [
        {"cta_code": "callback", "label": "📞 Request callback", "action_type": "lead"},
        {"cta_code": "website", "label": "🌐 Visit website", "action_type": "url", "action_value": "https://sgtas.ua"},
    ],
}


def run_category_labels_test() -> dict:
    checks = {
        "insurance": "Страхование" in AutomotivePartnerBrandingEngineV1.format_category_header(
            AutomotivePartnerType.INSURANCE.value, lang="ru"
        ),
        "credit": "Кредит" in AutomotivePartnerBrandingEngineV1.format_category_header(
            AutomotivePartnerType.CREDIT.value, lang="ru"
        ),
        "legal": "Юридическая" in AutomotivePartnerBrandingEngineV1.format_category_header(
            AutomotivePartnerType.LEGAL.value, lang="ru"
        ),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_partner_card_format_test() -> dict:
    text = AutomotivePartnerBrandingEngineV1.format_partner_card_text(SAMPLE_CARD)
    checks = {
        "has_name": "SG TAS" in text,
        "has_description": "Insurance leader" in text,
        "has_website": "sgtas.ua" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_logo_support_test() -> dict:
    photo = AutomotivePartnerBrandingEngineV1.partner_photo(SAMPLE_CARD)
    disabled = AutomotivePartnerBrandingEngineV1.partner_photo(
        {**SAMPLE_CARD, "branding": {**SAMPLE_CARD["branding"], "logo_enabled": False}}
    )
    checks = {
        "logo_url": photo == "https://sgtas.ua/logo.svg",
        "disabled_none": disabled is None,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_automotive_partner_branding_test_suite() -> dict:
    labels = run_category_labels_test()
    card = run_partner_card_format_test()
    logo = run_logo_support_test()
    ok = all(item.get("ok") for item in (labels, card, logo))
    return {"ok": ok, "labels": labels, "card": card, "logo": logo}


def run_automotive_partner_branding_tests() -> dict:
    return run_automotive_partner_branding_test_suite()
