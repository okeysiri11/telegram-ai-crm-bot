# Marketing Analytics v1 self-test.

from __future__ import annotations


def run_marketing_analytics_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_marketing_analytics_v1 import MarketingAnalyticsV1

        checks["engine"] = {
            "ok": hasattr(MarketingAnalyticsV1, "get_owner_metrics")
            and hasattr(MarketingAnalyticsV1, "resolve_marketing_source"),
            "detail": "metrics+resolve",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_marketing_analytics_v1 import MarketingAnalyticsV1
        from database.models.marketing_analytics_v1 import MarketingSourceKey

        fb = MarketingAnalyticsV1.resolve_marketing_source(utm_source="fb")
        boroda = MarketingAnalyticsV1.resolve_marketing_source(source_link="boroda_cars_promo")
        ref = MarketingAnalyticsV1.resolve_marketing_source(referral_code="partner42")
        checks["resolve"] = {
            "ok": fb == MarketingSourceKey.FACEBOOK.value
            and boroda == MarketingSourceKey.BORODA_CARS.value
            and ref == MarketingSourceKey.REFERRAL.value,
            "detail": f"{fb}/{boroda}/{ref}",
        }
    except Exception as exc:
        checks["resolve"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from database.models.marketing_analytics_v1 import MARKETING_SOURCE_DISPLAY

        checks["sources"] = {
            "ok": "Facebook" in MARKETING_SOURCE_DISPLAY.values()
            and "Boroda Cars" in MARKETING_SOURCE_DISPLAY.values(),
            "detail": "7 sources",
        }
    except Exception as exc:
        checks["sources"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_marketing_analytics_tests() -> dict:
    return run_marketing_analytics_test_suite()
