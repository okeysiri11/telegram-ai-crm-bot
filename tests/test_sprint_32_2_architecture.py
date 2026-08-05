"""Sprint 32.2 — Platform Core inventory, sprint review, foundations."""

from __future__ import annotations

from decimal import Decimal

from platform_architecture.core_inventory import inventory_summary, list_core_services, owner_for
from platform_architecture.service_constructor_foundation import universal_service_constructor
from platform_architecture.sprint_review import run_sprint_architecture_review
from services.pricing_foundation import pricing_foundation


def test_core_inventory_lists_required_services():
    services = {row["service"] for row in list_core_services()}
    required = {
        "event_bus",
        "workflow_runtime",
        "notification_service",
        "search_service",
        "permission_engine",
        "pricing_foundation",
        "catalog_engine",
    }
    assert required <= services
    assert inventory_summary()["composed_core"] is True
    assert inventory_summary()["platform_core_package"] is None
    assert owner_for("event_bus")["path"] == "events/event_bus.py"


def test_sprint_architecture_review_passes():
    report = run_sprint_architecture_review()
    assert report.passed, [f for f in report.findings if f.severity == "critical"]
    codes = {f.code for f in report.findings}
    assert "INVENTORY_OK" in codes
    assert "DEBT_REGISTRY_OK" in codes
    assert "COMPAT_OK" in codes or any(c.startswith("COMPAT_") for c in codes)


def test_pricing_foundation_quote():
    caps = pricing_foundation.capabilities()
    assert caps["tariffs"] and caps["ai_pricing"] and caps["foundation_only"]
    quote = pricing_foundation.quote(plan_id="growth", discount_code="LAUNCH10", ai_units=10)
    assert quote.currency == "USD"
    assert quote.discount > Decimal("0")
    assert quote.total > Decimal("0")
    assert "PricingEngine" in quote.meta["runtime_engine"]


def test_universal_service_constructor_foundation_no_ui():
    caps = universal_service_constructor.capabilities()
    assert caps["ui"] is False
    assert caps["service"] and caps["marketplace"]
    composed = universal_service_constructor.compose("svc_auto_listing")
    assert composed["ui_implemented"] is False
    assert composed["layers"]["presentation_ui"] is False
    assert len(composed["packages"]) >= 1
