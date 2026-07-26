"""Tests — Enterprise Consolidation / Web Preparation (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

CONSOLIDATION_DOCS = [
    "ENTERPRISE_CONSOLIDATION_30_3.md",
    "ARCHITECTURE_OWNERSHIP_GLOSSARY.md",
    "API_OWNERSHIP_REGISTRY.md",
    "AI_GROWTH_LAYER_BINDING.md",
    "DEPLOY_TOPOLOGY.md",
    "CRM_API_DEPRECATION.md",
    "WEB_PREPARATION_30_3.md",
    "CONSOLIDATION_INVENTORY_30_3.md",
    "IMPLEMENTATION_BACKLOG_30_3.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_consolidation_docs_exist():
    docs = ROOT / "docs"
    for name in CONSOLIDATION_DOCS:
        path = docs / name
        assert path.exists(), f"Missing: {name}"
        assert "30.3" in path.read_text()


def test_platform_compatible_after_consolidation():
    health = platform_builder.health()
    assert health["application_version"] == "1.48.0"
    assert health["sprint"] == "32.3.6"
    assert health["business_ecosystem_foundation_ready"] is True
    assert health["mission_control_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["mission_control"]["replaces_existing_modules"] is False
    assert health["business_ecosystem"]["does_not_replace_existing_modules"] is True


def test_web_portal_and_module_shells_exist():
    web = ROOT / "src" / "web"
    assert (web / "portals" / "PortalLayout.tsx").exists()
    assert (web / "portals" / "PortalPages.tsx").exists()
    assert (web / "workspace" / "pages" / "WorkspaceModulePage.tsx").exists()
    app = (web / "src" / "App.tsx").read_text()
    assert "/portals/customer" in app
    assert "/portals/employee" in app
    assert "/portals/owner" in app
    assert "/portals/mission-control" in app
    assert "/workspace/:module" in app
    assert "Command Center OS" in (web / "navigation" / "managers" / "menuEngine.ts").read_text()


def test_glossary_keeps_three_ecosystem_layers():
    glossary = (ROOT / "docs" / "ARCHITECTURE_OWNERSHIP_GLOSSARY.md").read_text()
    assert "/api/ecosystem/v1" in glossary
    assert "/api/ai-ecosystem/v1" in glossary
    assert "business-ecosystem" in glossary
    assert "Do **not** merge packages" in glossary or "Do not merge" in glossary


def test_crm_deprecation_does_not_remove():
    text = (ROOT / "docs" / "CRM_API_DEPRECATION.md").read_text()
    assert "still served" in text.lower() or "Deprecated" in text
    assert "Do **not** delete" in text or "Do not delete" in text


def test_backlog_next_is_web_implementation():
    backlog = (ROOT / "docs" / "IMPLEMENTATION_BACKLOG_30_3.md").read_text()
    assert "Web implementation" in backlog
    assert "Live identity bridge" in backlog
