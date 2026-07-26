"""Tests — Cafe Pilot Execution & Cross-Ecosystem Validation (Sprint 31.0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder
from applications.enterprise_hub import enterprise_hub


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "CAFE_PILOT_EXECUTION_31_0.md",
    "CAFE_INTEGRATION_31_0.md",
    "WORKFLOW_CAFE_31_0.md",
    "ECOSYSTEM_REUSE_MATRIX_31_0.md",
    "CAFE_PILOT_GUIDE_31_0.md",
    "PRODUCTION_STATUS_31_0.md",
    "RELEASE_NOTES_31_0.md",
    "SPRINT_REPORT_31_0.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    enterprise_hub.reset()
    yield
    platform_builder.reset()
    enterprise_hub.reset()


def test_cafe_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "31.0" in path.read_text()


def test_platform_cafe_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert health["release_status"] == "Enterprise Platform v1.0 Release Candidate"


def test_cafe_os_journey_and_eco_reuse():
    boot = enterprise_hub.cafe_os.bootstrap()
    assert boot.get("restaurant_id")
    assert boot.get("table_ids")
    assert enterprise_hub.health().get("cafe_os_ready") is True
    menu = enterprise_hub.cafe_os.list_menu()
    assert menu["count"] >= 1
    cust = enterprise_hub.cafe_os.create_customer(name="Guest 31", preferences=["31.0"])
    table_id = boot["table_ids"][0]
    rsv = enterprise_hub.cafe_os.reserve_table(
        table_id=table_id,
        customer_id=cust["customer_id"],
        party_size=2,
        start="2026-07-26T19:00:00Z",
    )
    item = menu["menu"][0]
    order = enterprise_hub.cafe_os.place_order(
        customer_id=cust["customer_id"],
        table_id=table_id,
        reservation_id=rsv["reservation_id"],
        items=[{"name": item["name"], "price": item["price"], "qty": 1}],
    )
    assert order.get("order_id") and order.get("kitchen_ticket_id")
    enterprise_hub.cafe_os.transition_kitchen(ticket_id=order["kitchen_ticket_id"], status="preparing")
    enterprise_hub.cafe_os.transition_kitchen(ticket_id=order["kitchen_ticket_id"], status="ready")
    enterprise_hub.commerce_core.bootstrap()
    pay = enterprise_hub.commerce_core.charge(
        provider="terminal", amount=order["total"], currency="USD", reference=order["order_id"]
    )
    assert pay.get("payment_id")
    loy = enterprise_hub.commerce_core.loyalty_profile(customer_id=cust["customer_id"], points=10)
    assert loy.get("loyalty_id")
    crm = enterprise_hub.cafe_os.crm_update(customer_id=cust["customer_id"], event="order_complete")
    assert crm.get("crm_event_id")
    assert enterprise_hub.cafe_os.qr_menu().get("url_path")
    assert enterprise_hub.cafe_os.dashboard().get("kpis")


def test_auto_beauty_unchanged_routes():
    web = ROOT / "src" / "web"
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/workspace/auto"' in app
    assert "AutomotiveLiveWorkflowPage" in app
    assert 'path="/workspace/beauty"' in app
    assert "BeautyLiveWorkflowPage" in app
    assert 'path="/workspace/cafe"' in app
    assert "CafeLiveWorkflowPage" in app
    # Beauty workflow file still present and not deleted
    assert (web / "workspace" / "beauty" / "beautyWorkflow.ts").exists()
    assert (web / "workspace" / "automotive" / "automotiveWorkflow.ts").exists()


def test_cafe_web_and_reuse_matrix():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "cafe" / "cafeWorkflow.ts").read_text()
    for needle in (
        "view_menu",
        "reserve_table",
        "place_order",
        "kitchen_queue",
        "commerceCorePrefix",
        "stepAiTeamConfigure",
        "quality_gates",
        "runCafeLiveWorkflow",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "34.0"' in cfg
    assert "cafeOsPrefix" in cfg
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "cafe: true" in tmpl
    assert "CROSS_ECOSYSTEM_PATTERNS" in tmpl
    assert "computeReusePercentage" in tmpl
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "cafeOs" in hub
    reg = (ROOT / "applications" / "enterprise_hub" / "api" / "register.py").read_text()
    assert "cafe_os_api_prefix" in reg
    assert "/kitchen" in reg


def test_reuse_docs_and_manifest():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_31_0.md").read_text()
    assert "100%" in text
    assert "Automotive" in text and "Beauty" in text and "Cafe" in text
    report = (ROOT / "docs" / "SPRINT_REPORT_31_0.md").read_text()
    assert "Agriculture" in report
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert "33.6" in manifest
    assert "Release Candidate" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "CAFE_PILOT_EXECUTION_31_0" in index
