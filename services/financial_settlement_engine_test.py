# Financial Settlement Engine v1 self-test.

from __future__ import annotations

from decimal import Decimal


def run_financial_settlement_test_suite() -> dict:
    checks: dict[str, dict] = {}

    try:
        from database.models.financial_settlement_engine_v1 import (
            FinancialSettlementV1Commission,
            FinancialSettlementV1Revenue,
            FinancialSettlementV1Settlement,
            FinancialSettlementV1TreasuryTransaction,
            FinancialTreasuryTransactionType,
        )
        from database.models.payment_engine_v1 import PaymentEngineStatus

        checks["tables"] = {
            "ok": (
                FinancialSettlementV1Revenue.__tablename__ == "financial_settlement_v1_revenues"
                and FinancialSettlementV1Settlement.__tablename__
                == "financial_settlement_v1_settlements"
                and FinancialSettlementV1Commission.__tablename__
                == "financial_settlement_v1_commissions"
                and FinancialSettlementV1TreasuryTransaction.__tablename__
                == "financial_settlement_v1_treasury_transactions"
            ),
            "detail": "4 tables",
        }
        checks["payment_status"] = {
            "ok": PaymentEngineStatus.SCREENSHOT_UPLOADED.value == "SCREENSHOT_UPLOADED",
            "detail": PaymentEngineStatus.UNDER_VERIFICATION.value,
        }
        checks["treasury_types"] = {
            "ok": FinancialTreasuryTransactionType.CLIENT_PAYMENT.value == "client_payment",
            "detail": "client_payment",
        }
    except Exception as exc:
        checks["tables"] = {"ok": False, "detail": str(exc)[:80]}

    try:
        from services.pg_financial_settlement_engine_v1 import FinancialSettlementEngineV1

        metrics = {
            "revenue_today": Decimal("100"),
            "revenue_week": Decimal("500"),
            "revenue_month": Decimal("2000"),
            "pending_settlements": 3,
            "partner_liabilities": Decimal("150"),
            "manager_commissions": Decimal("75"),
            "recent_settlements": [],
        }
        text = FinancialSettlementEngineV1.format_owner_settlement_analytics(metrics)
        checks["analytics"] = {
            "ok": "Today revenue: 100" in text and "Partner liabilities: 150" in text,
            "detail": "dashboard text",
        }
        settlement = {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "payment_id": "11111111-2222-3333-4444-555555555555",
            "deal_id": "66666666-7777-8888-9999-aaaaaaaaaaaa",
            "client_payment": "100.00",
            "partner_share": "30.00",
            "manager_share": "5.00",
            "platform_profit": "65.00",
            "currency": "USD",
            "status": "PENDING",
        }
        owner_text = FinancialSettlementEngineV1.format_owner_notification(settlement)
        mgr_text = FinancialSettlementEngineV1.format_manager_notification(settlement)
        checks["notifications"] = {
            "ok": "Platform profit: 65.00" in owner_text and "Your share: 5.00" in mgr_text,
            "detail": "notify text",
        }
    except Exception as exc:
        checks["analytics"] = {"ok": False, "detail": str(exc)[:80]}

    all_ok = all(item.get("ok") for item in checks.values())
    return {"ok": all_ok, "checks": checks}


def run_financial_settlement_tests() -> dict:
    return run_financial_settlement_test_suite()
