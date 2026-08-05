"""Tests — Enterprise Workflow Automation (Sprint 32.7)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_WORKFLOW_32_7.md",
    "RELEASE_NOTES_32_7.md",
]


def test_32_7_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.7" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_WORKFLOW_32_7" in index
    report = (docs / "ENTERPRISE_WORKFLOW_32_7.md").read_text()
    assert "No new Workflow Engine" in report or "No new Workflow" in report
    assert "Workflow Center" in report


def test_platform_version_32_7():
    health = platform_builder.health()
    assert health["application_version"] == "1.67.0"
    assert health["sprint"] == "1.1.1"
    assert health["release_status"] == "Enterprise Platform v1.1 General Availability"


def test_enterprise_workflow_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/workflow-center"' in app
    assert "WorkflowCenterPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "WorkflowAutomationWorkspace" in full
    city = (ROOT / "src" / "web" / "src" / "enterprise-city" / "EnterpriseCityPage.tsx").read_text()
    assert "ec-wf-route" in city
    assert "deriveWorkflowAutomation" in city
    templates = (
        ROOT / "src" / "web" / "src" / "enterprise-workflow" / "workflowTemplates.ts"
    ).read_text()
    for token in (
        "new_client",
        "sale",
        "contract",
        "project",
        "request",
        "crm_lead_processing",
        "contract_approval",
        "cityPath",
    ):
        assert token in templates
    derive = (
        ROOT / "src" / "web" / "src" / "enterprise-workflow" / "deriveWorkflowAutomation.ts"
    ).read_text()
    assert "deriveWorkflowAutomation" in derive
    panels = (
        ROOT / "src" / "web" / "src" / "enterprise-workflow" / "WorkflowAutomationPanels.tsx"
    ).read_text()
    for token in (
        "Workflow Center",
        "Workflow Timeline",
        "Workflow Monitor",
        "AI Chain",
        "Business Templates",
        "Executive View",
        "useLiveEnterprise",
    ):
        assert token in panels
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.7" in css
    assert "ewf-center" in css
    assert "ec-wf-route" in css
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "act_open_workflow_center" in qa


def test_config_manifest_32_7():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.67.0"' in cfg
    assert 'sprint: str = "1.1.1"' in cfg
    assert "General Availability" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.67.0"' in manifest
    assert '"sprint": "1.1.1"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "1.1.1"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.67.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "1.1.1"' in types
