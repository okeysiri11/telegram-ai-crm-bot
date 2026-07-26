"""Tests — Web Foundation & Production Stabilization (Sprint 30.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_DOCS = [
    "WEB_FOUNDATION_30_4.md",
    "WEB_ARCHITECTURE_30_4.md",
    "ROUTING_MAP_30_4.md",
    "MODULE_INTEGRATION_30_4.md",
    "API_STATUS_30_4.md",
    "PILOT_CHECKLIST_30_4.md",
    "PRODUCTION_READINESS_30_4.md",
    "DEPLOYMENT_NOTES_30_4.md",
    "IMPLEMENTATION_BACKLOG_30_4.md",
]

ECOSYSTEMS = ["auto", "beauty", "cafe", "agro", "drone", "legal", "crypto"]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_web_foundation_docs_exist():
    docs = ROOT / "docs"
    for name in FOUNDATION_DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        text = path.read_text()
        assert "30.4" in text
        assert len(text) > 200


def test_platform_web_foundation_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.39.0"
    assert health["sprint"] == "31.4"
    assert health["release_status"] == "Drone Ecosystem Completion"
    assert health["mission_control_ready"] is True
    assert health["business_ecosystem_foundation_ready"] is True
    assert health["mission_control"]["replaces_existing_modules"] is False
    assert health["business_ecosystem"]["does_not_replace_existing_modules"] is True


def test_module_registry_and_shell_files():
    web = ROOT / "src" / "web"
    registry = (web / "workspace" / "managers" / "moduleRegistry.ts").read_text()
    for key in ECOSYSTEMS:
        assert f"{key}:" in registry or f'"{key}"' in registry or f" {key}:" in registry
        assert f"/workspace/{key}" in registry or key in registry
    for key in ECOSYSTEMS:
        assert f'  {key}:' in registry or f"\n  {key}:" in registry

    assert (web / "src" / "integrations" / "telemetry.ts").exists()
    assert (web / "src" / "integrations" / "apiClient.ts").exists()
    assert (web / "src" / "shell" / "PermissionGuard.tsx").exists()

    menu = (web / "navigation" / "managers" / "menuEngine.ts").read_text()
    assert "nav_ecosystems" in menu
    assert "/workspace/cafe" in menu
    assert "/workspace/drone" in menu

    nav = (web / "navigation" / "managers" / "navigationManager.ts").read_text()
    assert "forTenant" in nav

    top = (web / "src" / "navigation" / "TopNavigation.tsx").read_text()
    assert "Mission Control" in top

    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "31.4"' in cfg
    assert "telemetryEnabled" in cfg


def test_pilot_checklist_covers_ecosystems():
    text = (ROOT / "docs" / "PILOT_CHECKLIST_30_4.md").read_text()
    for name in ("Automotive", "Beauty", "Cafe", "Agriculture", "Drone", "Legal", "Crypto"):
        assert name in text


def test_manifest_web_foundation():
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.39.0"' in manifest
    assert "31.4" in manifest
    assert "Drone Ecosystem Completion" in manifest


def test_audit_index_links_30_4():
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "WEB_FOUNDATION_30_4" in index
