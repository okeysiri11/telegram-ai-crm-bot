# Automotive Revenue Engine v1 tests.

from __future__ import annotations

from decimal import Decimal

from database.models.automotive_revenue_engine import REVENUE_SERVICE_TYPES
from services.pg_automotive_revenue_engine import (
    CommissionEngineV1,
    DEFAULT_LEAD_COMMISSION,
    AutomotiveRevenueEngineV1,
)


def run_service_types_test() -> dict:
    required = {
        "INSURANCE",
        "CREDIT",
        "LEASING",
        "LOGISTICS",
        "NOTARY",
        "LEGAL",
        "DEALER_REFERRAL",
    }
    checks = {name: name in REVENUE_SERVICE_TYPES for name in required}
    return {"ok": all(checks.values()), "checks": checks}


def run_commission_calculation_test() -> dict:
    flat_amount, rate = CommissionEngineV1.calculate_amount(service_type="INSURANCE")
    pct_amount, pct_rate = CommissionEngineV1.calculate_amount(
        service_type="CREDIT",
        base_amount=Decimal("100000"),
    )
    checks = {
        "flat_default": flat_amount == DEFAULT_LEAD_COMMISSION,
        "flat_rate": rate == Decimal("3.0"),
        "pct_amount": pct_amount == Decimal("1500.00"),
        "pct_rate": pct_rate == Decimal("1.5"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_dashboard_format_test() -> dict:
    sample = {
        "pending_commissions": [
            {
                "service_type": "INSURANCE",
                "amount": "500",
                "status": "PENDING",
            }
        ],
        "partner_settlements": [{"total": "1500", "status": "OPEN"}],
        "completed_deals": 3,
        "lifetime_value": "12000",
        "revenue_by_service": {"INSURANCE": "500"},
        "monthly_profit": {"2026-07": "8000"},
    }
    text = AutomotiveRevenueEngineV1.format_admin_dashboard(sample)
    checks = {
        "has_title": "Automotive Revenue Dashboard" in text,
        "has_pending": "Pending commissions" in text,
        "has_settlements": "Partner settlements" in text,
        "has_lifetime": "12000" in text,
        "has_service": "INSURANCE" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_engine_modules_test() -> dict:
    checks = {
        "record_customer_action": hasattr(AutomotiveRevenueEngineV1, "record_customer_action"),
        "get_admin_dashboard": hasattr(AutomotiveRevenueEngineV1, "get_admin_dashboard"),
        "lead_engine": hasattr(AutomotiveRevenueEngineV1, "LeadEngine"),
        "referral_engine": hasattr(AutomotiveRevenueEngineV1, "ReferralEngine"),
        "commission_engine": hasattr(AutomotiveRevenueEngineV1, "CommissionEngine"),
        "deal_engine": hasattr(AutomotiveRevenueEngineV1, "DealEngine"),
        "settlement_engine": hasattr(AutomotiveRevenueEngineV1, "PartnerSettlementEngine"),
        "analytics_engine": hasattr(AutomotiveRevenueEngineV1, "AnalyticsEngine"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_automotive_revenue_test_suite() -> dict:
    service_types = run_service_types_test()
    commission = run_commission_calculation_test()
    dashboard = run_dashboard_format_test()
    modules = run_engine_modules_test()
    ok = all(item.get("ok") for item in (service_types, commission, dashboard, modules))
    return {
        "ok": ok,
        "service_types": service_types,
        "commission": commission,
        "dashboard": dashboard,
        "modules": modules,
    }


def run_automotive_revenue_tests() -> dict:
    return run_automotive_revenue_test_suite()
