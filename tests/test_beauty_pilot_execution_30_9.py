"""Tests — Beauty Pilot Execution & Platform Reuse (Sprint 30.9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder
from applications.enterprise_hub import enterprise_hub


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "BEAUTY_PILOT_EXECUTION_30_9.md",
    "BEAUTY_PILOT_GUIDE_30_9.md",
    "ECOSYSTEM_REUSE_MATRIX_30_9.md",
    "WORKFLOW_BEAUTY_30_9.md",
    "API_STATUS_30_9.md",
    "PRODUCTION_STATUS_30_9.md",
    "KNOWN_ISSUES_30_9.md",
    "RELEASE_NOTES_30_9.md",
    "SPRINT_REPORT_30_9.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_beauty_execution_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        text = path.read_text()
        assert "30.9" in text
        assert len(text) > 150


def test_platform_beauty_execution_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.44.0"
    assert health["sprint"] == "32.3.2"
    assert health["release_status"] == "Enterprise Dashboard & Mission Control"


def test_bos_resources_extension_and_full_journey():
    bos = enterprise_hub.beauty_os.bootstrap()
    assert bos.get("resource_ids")
    listed = enterprise_hub.beauty_os.list_resources()
    assert listed["count"] >= 1
    room = enterprise_hub.beauty_os.create_resource(name="Exec Room", kind="room", branch=bos["branch_id"])
    assert room["resource_id"]
    branch = enterprise_hub.beauty_os.create_branch(
        name="Hours Floor",
        schedule={"mon": "09:00-20:00"},
        address="1 Pilot",
    )
    cust = enterprise_hub.beauty_os.create_customer(name="Exec Client", preferences=["30.9"])
    svc = enterprise_hub.beauty_os.create_service(
        name="Exec Cut", category="hair", duration_min=45, price=40
    )
    emp = enterprise_hub.beauty_os.create_employee(
        name="Exec Stylist", role="stylist", specialization="hair", services=["Exec Cut"]
    )
    book = enterprise_hub.beauty_client_journey.smart_book(
        channel="online",
        customer_id=cust["customer_id"],
        service_ids=[svc["service_id"]],
        employee_id=emp["employee_id"],
        branch_id=branch["branch_id"],
        auto_pick=True,
        duration_min=45,
    )
    aid = book.get("appointment_id")
    assert book.get("booking_id")
    if aid:
        enterprise_hub.beauty_os.transition_appointment(appointment_id=aid, status="confirmed")
        enterprise_hub.beauty_os.transition_appointment(appointment_id=aid, status="completed")
    enterprise_hub.commerce_core.bootstrap()
    pay = enterprise_hub.commerce_core.charge(
        provider="terminal", amount=40, currency="USD", reference=aid or book["booking_id"]
    )
    assert pay.get("payment_id")
    journey = enterprise_hub.beauty_client_journey.create_journey(
        customer_id=cust["customer_id"], source="pilot_30_9"
    )
    loyalty = enterprise_hub.beauty_client_journey.loyalty_scan(journey_id=journey["journey_id"])
    assert loyalty.get("loyalty_id")


def test_ai_team_configure_reusable():
    dash = platform_builder.ai_team.dashboard("org_beauty_30_9")
    assert dash.get("ready") is True
    assert dash.get("members")
    agent_id = dash["members"][0]["agent_id"]
    out = platform_builder.ai_team.action(
        "org_beauty_30_9",
        agent_id,
        "assign_task",
        {"task": "[beauty] Confirm bookings"},
    )
    assert out


def test_beauty_execution_web_and_reuse():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "beauty" / "beautyWorkflow.ts").read_text()
    for needle in (
        "choose_service",
        "choose_specialist",
        "calendar",
        "booking",
        "confirmation",
        "reminder",
        "visit",
        "crm_update",
        "stepAiTeamConfigure",
        "commerceCorePrefix",
        "/resources",
        "quality_gates",
        "computeReusePercentage",
    ):
        assert needle in wf, needle
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "computeReusePercentage" in tmpl
    assert "stepAiTeamConfigure" in tmpl
    assert "shared_ai" in tmpl
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.3.2"' in cfg
    assert "commerceCorePrefix" in cfg
    page = (web / "workspace" / "beauty" / "BeautyLiveWorkflowPage.tsx").read_text()
    assert "Reuse" in page
    assert "computeReusePercentage" in page
    # Automotive still present
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/workspace/auto"' in app
    assert 'path="/workspace/beauty"' in app
    register = (ROOT / "applications" / "enterprise_hub" / "api" / "register.py").read_text()
    assert f'{{bos}}/resources' in register or "/resources" in register


def test_reuse_matrix_is_full():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_30_9.md").read_text()
    assert "100%" in text
    assert "16/16" in text
    report = (ROOT / "docs" / "SPRINT_REPORT_30_9.md").read_text()
    assert "Cafe" in report
    assert "Architecture unchanged" in report or "architecture unchanged" in report.lower()


def test_manifest_and_index():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.44.0"' in manifest
    assert "32.3.2" in manifest
    assert "Enterprise Dashboard & Mission Control" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "BEAUTY_PILOT_EXECUTION_30_9" in index
