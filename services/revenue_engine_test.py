# Universal Revenue Engine v1 self-test.

from __future__ import annotations

from decimal import Decimal


def run_revenue_engine_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.revenue_engine_v1 import RevenueEngineV1Entry, RevenueEngineV1PaymentStatus

        checks["model"] = {
            "ok": RevenueEngineV1Entry.__tablename__ == "revenue_engine_v1_entries",
            "detail": RevenueEngineV1Entry.__tablename__,
        }
        checks["payment_status"] = {
            "ok": RevenueEngineV1PaymentStatus.PAID.value == "PAID",
            "detail": RevenueEngineV1PaymentStatus.PAID.value,
        }
    except Exception as exc:
        checks["model"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_revenue_engine_v1 import RevenueEngineV1
        from database.models.deal_engine_v1 import DealEngineV1Deal

        deal = DealEngineV1Deal(
            vertical="auto",
            client_id=__import__("uuid").uuid4(),
            title="Test",
            amount=Decimal("10000"),
            currency="USD",
            status="COMPLETED",
        )
        deal.partner_id = __import__("uuid").uuid4()
        deal.manager_id = __import__("uuid").uuid4()
        split = RevenueEngineV1._calculate_split(deal, has_referral=True)
        total = (
            split["platform_income"]
            + split["partner_income"]
            + split["manager_income"]
            + split["referral_income"]
        )
        checks["split"] = {
            "ok": split["gross_amount"] == total,
            "detail": str(split["platform_income"]),
        }
        checks["engine"] = {
            "ok": hasattr(RevenueEngineV1, "create_from_completed_deal"),
            "detail": "create_from_completed_deal",
        }
    except Exception as exc:
        checks["split"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_revenue_engine_tests() -> dict:
    return run_revenue_engine_test_suite()
