"""Tests — First Live Workflow & Pilot Execution (Sprint 30.6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder
from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.crm.models import CRMLead, CustomerProfile, LeadSource


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "FIRST_LIVE_WORKFLOW_30_6.md",
    "AUTHENTICATION_GUIDE_30_6.md",
    "WORKFLOW_AUTOMOTIVE_30_6.md",
    "PILOT_REPORT_30_6.md",
    "API_STATUS_30_6.md",
    "WEB_STATUS_30_6.md",
    "PRODUCTION_STATUS_30_6.md",
    "NEXT_ECOSYSTEM_READINESS_30_6.md",
    "IMPLEMENTATION_BACKLOG_30_6.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_live_workflow_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        text = path.read_text()
        assert "30.6" in text
        assert len(text) > 150


def test_platform_first_live_workflow_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.34.0"
    assert health["sprint"] == "30.9"
    assert health["release_status"] == "Beauty Pilot Execution"
    assert health["mission_control_ready"] is True


def test_production_auth_and_workflow_web_files():
    web = ROOT / "src" / "web"
    assert (web / "src" / "auth" / "identityApi.ts").exists()
    auth = (web / "src" / "auth" / "authStore.ts").read_text()
    assert "productionLogin" in auth
    assert ".demo" in auth  # rejection of demo tokens
    assert "refreshSession" in auth
    assert (web / "workspace" / "automotive" / "AutomotiveLiveWorkflowPage.tsx").exists()
    assert (web / "workspace" / "automotive" / "automotiveWorkflow.ts").exists()
    wf = (web / "workspace" / "automotive" / "automotiveWorkflow.ts").read_text()
    for needle in (
        "/portal/auth/",
        "/crm/customers",
        "/crm/leads",
        "/concierge/sessions",
        "/crm/tasks",
        "/timeline",
        "/center",
        "mission-control",
        "/crm/pipeline",
        "quality_gates",
    ):
        assert needle in wf
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/workspace/auto"' in app
    assert "AutomotiveLiveWorkflowPage" in app
    vite = (web / "vite.config.ts").read_text()
    assert '"/management"' in vite


def test_crm_lead_nba_path_reusable():
    """Existing Automotive CRM APIs support the live workflow core."""
    import asyncio

    async def _run():
        profile = CustomerProfile(first_name="Pilot", last_name="User", email="pilot30_6@demo.corp")
        cust = await auto_marketplace.crm_engine.customers.create(profile)
        lead = CRMLead(
            customer_id=cust.customer_id,
            vehicle_id="veh_pilot",
            dealer_id="dealer_pilot",
            source=LeadSource.WEB,
            notes="sprint 30.6",
        )
        created_lead = await auto_marketplace.crm_engine.leads.create(lead, cust)
        nba = await auto_marketplace.crm_engine.ai.next_best_action(created_lead)
        return cust, created_lead, nba

    cust, lead, nba = asyncio.run(_run())
    assert cust.customer_id
    assert lead.lead_id
    assert nba is not None


def test_next_ecosystem_readiness_lists_blockers_only():
    text = (ROOT / "docs" / "NEXT_ECOSYSTEM_READINESS_30_6.md").read_text()
    for name in ("Beauty", "Cafe", "Agriculture", "Drone", "Legal", "Crypto"):
        assert name in text
    assert "No redesign" in text or "no implementation" in text.lower()


def test_manifest_and_audit_index():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.34.0"' in manifest
    assert "30.9" in manifest
    assert "Beauty Pilot Execution" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "FIRST_LIVE_WORKFLOW_30_6" in index
