"""Tests — Enterprise Integration Hub (Sprint 33.1)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_INTEGRATION_HUB_33_1.md",
    "RELEASE_NOTES_33_1.md",
]


def test_33_1_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.1" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_INTEGRATION_HUB_33_1" in index
    report = (docs / "ENTERPRISE_INTEGRATION_HUB_33_1.md").read_text()
    assert "No new Integration Engine" in report
    assert "Connection Wizard" in report
    assert "Telegram" in report


def test_platform_version_33_1():
    health = platform_builder.health()
    assert health["application_version"] == "1.58.0"
    assert health["sprint"] == "33.2"
    assert "AI Runtime & Orchestration Center" in health["release_status"]


def test_integration_hub_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/integrations"' in app
    assert "EnterpriseIntegrationHubPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "IntegrationHubStrip" in full
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-integrations" / "integrationCatalog.ts").read_text()
    for token in (
        "Telegram",
        "WhatsApp",
        "Email",
        "SMS",
        "Web Widget",
        "Push Notifications",
        "CRM",
        "ERP",
        "Accounting",
        "Payment Systems",
        "Document Management",
        "Calendar",
        "Storage",
        "REST API",
        "Webhooks",
        "OAuth",
        "API Keys",
        "SDK",
    ):
        assert token in catalog
    page = (
        ROOT / "src" / "web" / "src" / "enterprise-integrations" / "EnterpriseIntegrationHubPage.tsx"
    ).read_text()
    for token in (
        "Integration Dashboard",
        "Integration Monitor",
        "Connection Wizard",
        "BuilderStepNav",
        "ProgressIndicator",
        "Enterprise Digital Twin",
    ):
        assert token in page
    css = (ROOT / "src" / "web" / "src" / "enterprise-integrations" / "enterprise-integrations.css").read_text()
    assert "Sprint 33.1" in css
    assert "eih-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-integrations.css" in idx
    twin = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    assert "deriveIntegrationHub" in twin
    assert "External Systems" in twin
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/integrations" in qa


def test_config_manifest_33_1():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.58.0"' in cfg
    assert 'sprint: str = "33.2"' in cfg
    assert "AI Runtime & Orchestration Center" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.58.0"' in manifest
    assert '"sprint": "33.2"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.2"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.58.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.2"' in types
