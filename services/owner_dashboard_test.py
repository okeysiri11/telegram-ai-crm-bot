# Owner Dashboard v1 self-test.

from __future__ import annotations


def run_owner_dashboard_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from services.pg_owner_dashboard_engine import OwnerDashboardEngineV1

        checks["engine"] = {
            "ok": hasattr(OwnerDashboardEngineV1, "get_dashboard")
            and hasattr(OwnerDashboardEngineV1, "format_main_dashboard"),
            "detail": "dashboard+format",
        }
    except Exception as exc:
        checks["engine"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from repositories.owner_dashboard_repository import OwnerDashboardRepository

        sample = {
            "auto": {"leads": 10, "leads_month": 3, "deals": 5, "deals_completed": 2, "revenue": 1000, "revenue_month": 400},
            "agro": {"leads": 4, "leads_month": 1, "deals": 2, "deals_completed": 1, "revenue": 200, "revenue_month": 80},
            "global": {
                "total_income": 1200,
                "total_income_month": 480,
                "total_income_today": 50,
                "commissions": 300,
                "commissions_month": 120,
                "top_partners": [("direct", 0, 0)],
                "top_managers": [("unassigned", 0, 0)],
            },
            "marketing": {"leads_today": 1, "leads_month": 4, "by_source": [], "by_utm": []},
            "revenue_detail": {"gross": 500, "platform": 300, "partner": 100, "manager": 50, "referral": 50},
        }
        from services.pg_owner_dashboard_engine import OwnerDashboardEngineV1

        text = OwnerDashboardEngineV1.format_main_dashboard(sample)
        checks["format"] = {
            "ok": "AUTO" in text and "AGRO" in text and "Global" in text,
            "detail": "main dashboard",
        }
    except Exception as exc:
        checks["format"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_owner_dashboard_tests() -> dict:
    return run_owner_dashboard_test_suite()
