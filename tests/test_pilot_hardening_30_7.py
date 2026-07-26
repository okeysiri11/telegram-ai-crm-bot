"""Tests — Pilot Hardening & Production Feedback Loop (Sprint 30.7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "PILOT_HARDENING_30_7.md",
    "PILOT_GUIDE_30_7.md",
    "PILOT_FEEDBACK_30_7.md",
    "KNOWN_ISSUES_30_7.md",
    "RELEASE_NOTES_30_7.md",
    "DEPLOYMENT_GUIDE_30_7.md",
    "PRODUCTION_CHECKLIST_30_7.md",
    "IMPLEMENTATION_BACKLOG_30_7.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_pilot_hardening_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        assert "30.7" in path.read_text()


def test_platform_pilot_hardening_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.52.0"
    assert health["sprint"] == "32.6"
    assert health["release_status"] == "AI Team Collaboration & Multi-Agent Workspace"


def test_feedback_metrics_journeys_web():
    web = ROOT / "src" / "web"
    assert (web / "src" / "integrations" / "pilotFeedback.ts").exists()
    assert (web / "src" / "integrations" / "pilotMetrics.ts").exists()
    assert (web / "src" / "pilot" / "roleJourneys.ts").exists()
    fb = (web / "src" / "integrations" / "pilotFeedback.ts").read_text()
    assert "enterprise-epr/v1" in fb
    assert "enterprise-ele/v1" in fb
    assert "Critical" in fb
    assert "assignModule" in fb
    journeys = (web / "src" / "pilot" / "roleJourneys.ts").read_text()
    for role in ("owner", "manager", "sales", "employee", "customer"):
        assert role in journeys
    pilot = (web / "src" / "pages" / "PilotDashboardPage.tsx").read_text()
    assert "submitPilotFeedback" in pilot
    assert "validateJourneys" in pilot
    assert "pilotMetrics" in pilot
    assert "business" in pilot
    wf = (web / "workspace" / "automotive" / "automotiveWorkflow.ts").read_text()
    assert "customer_timeline" in wf
    assert "quality_gates" in wf
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "pilotReadiness" in hub
    assert "learningEngine" in hub


def test_epr_feedback_api_still_central():
    """Do not invent a parallel feedback API — EPR remains the entry."""
    api = (ROOT / "applications" / "enterprise_hub" / "pilot_readiness" / "api.py").read_text()
    assert "epr_feedback_handler" in api
    assert "submit_feedback" in api


def test_manifest_and_index():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.52.0"' in manifest
    assert "32.6" in manifest
    assert "AI Team Collaboration & Multi-Agent Workspace" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "PILOT_HARDENING_30_7" in index
