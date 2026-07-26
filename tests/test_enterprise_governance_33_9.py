"""Tests — Enterprise Governance (Sprint 33.9)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_GOVERNANCE_33_9.md",
    "RELEASE_NOTES_33_9.md",
]


def test_33_9_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.9" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_GOVERNANCE_33_9" in index
    report = (docs / "ENTERPRISE_GOVERNANCE_33_9.md").read_text()
    assert "No new RBAC" in report
    assert "Policy Validation" in report
    assert "Executive Approval Center" in report
    assert "AI Governance" in report


def test_platform_version_33_9():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert "Release Candidate" in health["release_status"]


def test_governance_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/governance"' in app
    assert "EnterpriseGovernancePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "GovernanceStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "enterprise-governance" / "deriveGovernance.ts").read_text()
    for token in (
        "deriveGovernance",
        "PolicyValidation",
        "approvalQueue",
        "auditTimeline",
        "aiGovernance",
        "deriveAutonomy",
        "listApprovals",
        "matchPolicy",
    ):
        assert token in derive
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-governance" / "policiesCatalog.ts").read_text()
    for token in (
        "financial",
        "security",
        "legal",
        "privacy",
        "hr",
        "operations",
        "ai_usage",
        "automation",
    ):
        assert token in catalog
    page = (
        ROOT / "src" / "web" / "src" / "enterprise-governance" / "EnterpriseGovernancePage.tsx"
    ).read_text()
    for token in (
        "Enterprise Policies",
        "Policy Validation",
        "Executive Approval Center",
        "Enterprise Audit Timeline",
        "Risk Dashboard",
        "AI Governance",
        "Compliance Center",
        "GovernanceWidgetCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "enterprise-governance" / "enterprise-governance.css"
    ).read_text()
    assert "Sprint 33.9" in css
    assert "gov-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-governance.css" in idx
    search = (ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts").read_text()
    assert "idx_governance" in search
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/governance" in qa
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "GovernanceWidgetCompact" in mc
    # Existing autonomy approval center preserved
    assert 'path="/platform-builder/autonomy"' in app


def test_config_manifest_33_9():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.66.0"' in cfg
    assert 'sprint: str = "34.0"' in cfg
    assert "Release Candidate" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert '"sprint": "34.0"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "34.0"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.66.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "34.0"' in types
