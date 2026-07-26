"""Tests — Web Core Integration & First Pilot Readiness (Sprint 30.5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

CORE_DOCS = [
    "WEB_CORE_30_5.md",
    "WEB_INTEGRATION_GUIDE_30_5.md",
    "MODULE_REGISTRY_30_5.md",
    "ROUTING_30_5.md",
    "PILOT_GUIDE_30_5.md",
    "DEPLOYMENT_GUIDE_30_5.md",
    "ARCHITECTURE_INVENTORY_30_5.md",
    "TECHNICAL_DEBT_30_5.md",
    "PRODUCTION_READINESS_30_5.md",
    "IMPLEMENTATION_BACKLOG_30_5.md",
]

ECOSYSTEMS = ["auto", "beauty", "cafe", "agro", "drone", "legal", "crypto"]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_web_core_docs_exist():
    docs = ROOT / "docs"
    for name in CORE_DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        text = path.read_text()
        assert "30.5" in text
        assert len(text) > 150


def test_platform_web_core_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.57.0"
    assert health["sprint"] == "33.1"
    assert health["release_status"] == "Enterprise Integration Hub"
    assert health["mission_control_ready"] is True
    assert health["business_ecosystem_foundation_ready"] is True
    assert health["mission_control"]["replaces_existing_modules"] is False


def test_module_registry_full_shape_and_ecosystems():
    registry = (ROOT / "src" / "web" / "workspace" / "managers" / "moduleRegistry.ts").read_text()
    assert "RegisteredModule" in registry
    assert "listRegistered" in registry
    assert "ecosystemsRegistered" in registry
    assert "healthSummary" in registry
    for field in (
        "version",
        "routes",
        "permissions",
        "navigation",
        "widgets",
        "dashboards",
        "dependencies",
        "health",
    ):
        assert field in registry
    for key in ECOSYSTEMS:
        assert f'"{key}"' in registry or f"{key}:" in registry or f'entry("{key}"' in registry


def test_pilot_dashboard_and_mission_control_live():
    web = ROOT / "src" / "web"
    assert (web / "src" / "pages" / "PilotDashboardPage.tsx").exists()
    assert (web / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx").exists()
    assert (web / "src" / "shell" / "WebCoreProvider.tsx").exists()
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/pilot"' in app
    assert "PilotDashboardPage" in app
    studio = (web / "platform-builder" / "mission-control" / "MissionControlStudio.tsx").read_text()
    assert "MissionControlLivePanel" in studio
    menu = (web / "navigation" / "managers" / "menuEngine.ts").read_text()
    assert 'route: "/pilot"' in menu


def test_shared_ui_and_observability_extensions():
    web = ROOT / "src" / "web"
    assert (web / "src" / "ui" / "sharedUi.ts").exists()
    assert (web / "src" / "ui" / "EmptyState.tsx").exists()
    telemetry = (web / "src" / "integrations" / "telemetry.ts").read_text()
    assert "healthSnapshot" in telemetry
    assert "businessEvent" in telemetry
    apps = (web / "navigation" / "managers" / "applicationRegistry.ts").read_text()
    assert "fromModule" in apps or "moduleRegistry" in apps
    assert "pilot_dashboard" in apps


def test_manifest_and_audit_index():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.57.0"' in manifest
    assert "33.1" in manifest
    assert "Enterprise Integration Hub" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "WEB_CORE_30_5" in index


def test_production_readiness_verdict():
    text = (ROOT / "docs" / "PRODUCTION_READINESS_30_5.md").read_text()
    assert "internal pilot" in text.lower()
    assert "Pilot Dashboard" in text
