"""Tests — Business Ecosystem Template & Beauty Pilot Foundation (Sprint 30.8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder
from applications.enterprise_hub import enterprise_hub


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "BEAUTY_PILOT_30_8.md",
    "BEAUTY_INTEGRATION_30_8.md",
    "WORKFLOW_BEAUTY_30_8.md",
    "ECOSYSTEM_REUSE_MATRIX_30_8.md",
    "API_STATUS_30_8.md",
    "PILOT_CHECKLIST_30_8.md",
    "BEAUTY_PILOT_READINESS_30_8.md",
    "RELEASE_NOTES_30_8.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_beauty_pilot_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        text = path.read_text()
        assert "30.8" in text
        assert len(text) > 150


def test_platform_beauty_pilot_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.34.0"
    assert health["sprint"] == "30.9"
    assert health["release_status"] == "Beauty Pilot Execution"


def test_beauty_hub_apis_reusable():
    """Beauty domain APIs already exist on Hub — workflow reconnects, does not fork."""
    bos = enterprise_hub.beauty_os.bootstrap()
    assert bos.get("company_id")
    assert bos.get("branch_id")
    cust = enterprise_hub.beauty_os.create_customer(name="Pilot Client", preferences=["30.8"])
    assert cust.get("customer_id")
    svc = enterprise_hub.beauty_os.create_service(
        name="Pilot Haircut", category="hair", duration_min=45, price=40
    )
    assert svc.get("service_id")
    emp = enterprise_hub.beauty_os.create_employee(
        name="Pilot Stylist", role="stylist", specialization="hair", services=["Pilot Haircut"]
    )
    assert emp.get("employee_id")
    book = enterprise_hub.beauty_client_journey.smart_book(
        channel="online",
        customer_id=cust["customer_id"],
        service_ids=[svc["service_id"]],
        employee_id=emp["employee_id"],
        branch_id=bos["branch_id"],
        auto_pick=True,
        duration_min=45,
    )
    assert book.get("booking_id")
    journey = enterprise_hub.beauty_client_journey.create_journey(
        customer_id=cust["customer_id"], source="pilot_30_8"
    )
    assert journey.get("journey_id")
    dash = enterprise_hub.beauty_os.dashboard()
    assert dash.get("dashboard_id") or dash
    bws = enterprise_hub.beauty_workspace.bootstrap()
    assert bws
    schedule = enterprise_hub.beauty_workspace.schedule(view="day")
    assert schedule is not None


def test_ecosystem_template_and_beauty_web():
    web = ROOT / "src" / "web"
    assert (web / "workspace" / "ecosystem-template" / "index.ts").exists()
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "ECOSYSTEM_REUSE_MATRIX" in tmpl
    assert "stepAiConcierge" in tmpl
    assert "stepMissionControl" in tmpl
    assert "stepObservability" in tmpl
    assert (web / "workspace" / "beauty" / "BeautyLiveWorkflowPage.tsx").exists()
    assert (web / "workspace" / "beauty" / "beautyWorkflow.ts").exists()
    wf = (web / "workspace" / "beauty" / "beautyWorkflow.ts").read_text()
    for needle in (
        "beautyOsPrefix",
        "beautyWorkspacePrefix",
        "beautyClientJourneyPrefix",
        "/book",
        "/schedule",
        "/journey",
        "/assistant",
        "stepAiConcierge",
        "stepMissionControl",
        "quality_gates",
        "runBeautyLiveWorkflow",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert "beautyOsPrefix" in cfg
    assert "beautyWorkspacePrefix" in cfg
    assert "beautyClientJourneyPrefix" in cfg
    assert "aiMarketingOsPrefix" in cfg
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/workspace/beauty"' in app
    assert "BeautyLiveWorkflowPage" in app
    # Automotive remains present (unchanged route)
    assert 'path="/workspace/auto"' in app
    assert "AutomotiveLiveWorkflowPage" in app
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "beautyOs" in hub
    assert "beautyWorkspace" in hub
    assert "beautyClientJourney" in hub
    reg = (web / "workspace" / "managers" / "moduleRegistry.ts").read_text()
    assert "enterprise-bos" in reg
    journeys = (web / "src" / "pilot" / "roleJourneys.ts").read_text()
    assert "/workspace/beauty" in journeys
    pilot = (web / "src" / "pages" / "PilotDashboardPage.tsx").read_text()
    assert "/workspace/beauty" in pilot
    fb = (web / "src" / "integrations" / "pilotFeedback.ts").read_text()
    assert '"beauty"' in fb or "beauty:" in fb

def test_reuse_matrix_documents_shared_platform():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_30_8.md").read_text()
    for cap in (
        "Authentication",
        "Authorization",
        "Workspace",
        "Mission Control",
        "Knowledge",
        "Workflow engine",
        "Notification",
        "Telemetry",
        "AI platform",
    ):
        assert cap in text
    assert "Automotive" in text and "Beauty" in text


def test_manifest_and_audit_index():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.34.0"' in manifest
    assert "30.9" in manifest
    assert "Beauty Pilot Execution" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "BEAUTY_PILOT_30_8" in index
