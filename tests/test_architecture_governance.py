"""Architecture governance tests — executable contracts and CI failure behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from platform_architecture.api_validator import validate_api
from platform_architecture.boundary_validator import validate_boundaries
from platform_architecture.certification import certify
from platform_architecture.dependency_graph import build_dependency_graph, graph_violations
from platform_architecture.governance import ArchitectureGovernance
from platform_architecture.import_scanner import scan_all_imports, critical_import_violations
from platform_architecture.plugin_validator import validate_plugins
from platform_architecture.report_generator import (
    generate_architecture_certificate,
    generate_architecture_report,
)
from platform_architecture.rules import LEGACY_HANDLER_VIOLATIONS_ALLOWLIST, ArchitectureViolation, ViolationSeverity
from platform_architecture.sdk_validator import validate_sdk
from platform_architecture.workflow_validator import validate_workflows
from src.platform.layers.architecture_policy import scan_file

ROOT = Path(__file__).resolve().parents[1]


def test_governance_passes_on_current_codebase():
    report = ArchitectureGovernance(ROOT).run_all(write_reports=False)
    assert report.certification.architecture_score >= 90, report.certification.gate_failures
    assert report.passed, report.certification.gate_failures


def test_forbidden_plugin_repository_import_detected(tmp_path: Path):
    bad = tmp_path / "plugins" / "demo" / "plugin.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from repositories.user_repository import UserRepository\n", encoding="utf-8")
    violations = scan_file(bad, root=tmp_path)
    assert any(v.rule == "plugin_no_repository" for v in violations)


def test_management_db_import_detected(tmp_path: Path):
    bad = tmp_path / "platform_management" / "bad.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from database.session import get_session\n", encoding="utf-8")
    violations = scan_file(bad, root=tmp_path)
    assert any(v.rule == "management_no_database" for v in violations)


def test_boundary_validation_passes():
    summary = validate_boundaries(ROOT)
    critical = [v for v in summary.violations if v.severity == ViolationSeverity.CRITICAL]
    assert not critical, [f"{v.rule} {v.path}" for v in critical]


def test_plugin_validation_passes():
    summary = validate_plugins(ROOT)
    assert summary.passed, summary.violations


def test_workflow_validation_passes():
    summary = validate_workflows(ROOT)
    assert summary.passed, summary.violations
    assert summary.total_checks >= 1


def test_api_validation_passes():
    summary = validate_api(ROOT)
    assert summary.passed, summary.violations


def test_sdk_validation_passes():
    summary = validate_sdk(ROOT)
    assert summary.passed, summary.violations


def test_dependency_graph_builds():
    graph = build_dependency_graph(ROOT)
    assert graph.node_count > 10
    assert graph.edge_count >= 0


def test_dependency_graph_detects_cycle(tmp_path: Path):
    mgmt = tmp_path / "platform_management"
    mgmt.mkdir()
    (mgmt / "management_router.py").write_text(
        "from database.engine import check_db_health\n",
        encoding="utf-8",
    )
    db = tmp_path / "database"
    db.mkdir()
    (db / "__init__.py").write_text("", encoding="utf-8")
    (db / "engine.py").write_text(
        "from platform_management.management_router import register_management_routes\n",
        encoding="utf-8",
    )
    graph = build_dependency_graph(tmp_path)
    issues = graph_violations(graph)
    assert any(v.rule == "dependency_cycle" for v in issues)


def test_report_generation(tmp_path: Path):
    graph = build_dependency_graph(ROOT)
    summaries = [
        validate_boundaries(ROOT),
        validate_plugins(ROOT),
        validate_workflows(ROOT),
    ]
    certification = certify(summaries=summaries, graph=graph, legacy_ok=True)
    report_path = generate_architecture_report(
        summaries=summaries,
        graph=graph,
        certification=certification,
        output_path=tmp_path / "ARCHITECTURE_REPORT.md",
    )
    cert_path = generate_architecture_certificate(
        certification,
        output_path=tmp_path / "ARCHITECTURE_CERTIFICATE.md",
    )
    assert report_path.is_file()
    assert cert_path.is_file()
    assert "Architecture Report" in report_path.read_text(encoding="utf-8")
    assert "Architecture Certificate" in cert_path.read_text(encoding="utf-8")


def test_ci_fails_on_violation(tmp_path: Path):
    bad = tmp_path / "platform_management" / "leak.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from repositories import user_repository\n", encoding="utf-8")
    summary = validate_boundaries(tmp_path)
    assert not summary.passed


def test_legacy_handler_allowlist_tracked():
    violations = scan_all_imports(ROOT)
    handler_keys = {
        v.key()
        for v in violations
        if v.rule == "handler_no_database" and v.path in {
            "auto_vertical_handlers.py",
            "automotive_partner_handlers.py",
            "dealer_onboarding_handlers.py",
            "handlers.py",
        }
    }
    assert handler_keys == LEGACY_HANDLER_VIOLATIONS_ALLOWLIST


def test_critical_import_filter_respects_allowlist():
    violations = scan_all_imports(ROOT)
    critical = critical_import_violations(violations)
    for item in critical:
        assert item.key() not in LEGACY_HANDLER_VIOLATIONS_ALLOWLIST


def test_governance_assert_clean():
    ArchitectureGovernance(ROOT).assert_clean()
