"""Tests — Enterprise Data Fabric & Knowledge Graph (Sprint 33.3)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_DATA_FABRIC_33_3.md",
    "RELEASE_NOTES_33_3.md",
]


def test_33_3_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.3" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_DATA_FABRIC_33_3" in index
    report = (docs / "ENTERPRISE_DATA_FABRIC_33_3.md").read_text()
    assert "No new Database Engine" in report
    assert "Relationship Explorer" in report
    assert "Data Lineage" in report


def test_platform_version_33_3():
    health = platform_builder.health()
    assert health["application_version"] == "1.59.0"
    assert health["sprint"] == "33.3"
    assert "Data Fabric" in health["release_status"]


def test_data_fabric_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/data-fabric"' in app
    assert "EnterpriseDataFabricPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "DataFabricStrip" in full
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-data-fabric" / "fabricCatalog.ts").read_text()
    for token in (
        "Companies",
        "Users",
        "AI Team",
        "Clients",
        "Deals",
        "Documents",
        "Workflows",
        "Knowledge",
        "Integrations",
        "KNOWLEDGE_CHAIN",
    ):
        assert token in catalog
    page = (
        ROOT / "src" / "web" / "src" / "enterprise-data-fabric" / "EnterpriseDataFabricPage.tsx"
    ).read_text()
    for token in (
        "Enterprise Graph",
        "Relationship Explorer",
        "Data Lineage",
        "Knowledge Connections",
        "Impact Analysis",
        "DataFabricOverviewCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "enterprise-data-fabric" / "enterprise-data-fabric.css"
    ).read_text()
    assert "Sprint 33.3" in css
    assert "edf-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-data-fabric.css" in idx
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "DataFabricOverviewCompact" in mc
    twin = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    assert "deriveDataFabric" in twin
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/data-fabric" in qa


def test_config_manifest_33_3():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.59.0"' in cfg
    assert 'sprint: str = "33.3"' in cfg
    assert "Enterprise Data Fabric & Knowledge Graph" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.59.0"' in manifest
    assert '"sprint": "33.3"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.3"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.59.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.3"' in types
