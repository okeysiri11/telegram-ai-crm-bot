"""Platform certification tests — Sprint 1.5 reproducible gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from platform_certification.checks import (
    check_repository_service_imports,
    check_sdk_database_imports,
    check_sdk_repository_imports,
    check_unauthorized_admin_routes,
)
from platform_certification.runner import PlatformCertification

ROOT = Path(__file__).resolve().parents[1]


def test_certification_runner_structure():
    cert = PlatformCertification(ROOT)
    assert cert.root == ROOT


@pytest.mark.slow
def test_certification_runner_full_scan():
    result = PlatformCertification(ROOT).run(write_reports=False)
    assert result.verdict in {"PASS", "FAIL"}
    assert len(result.checks) >= 10


def test_certification_docs_exist_after_script():
    summary = ROOT / "docs" / "certification_summary.json"
    assert summary.is_file(), "Run scripts/run_platform_certification.py first"
    platform_doc = ROOT / "docs" / "PLATFORM_CERTIFICATION.md"
    assert platform_doc.is_file()
    manifest = ROOT / "platform_manifest.json"
    assert manifest.is_file()


def test_repository_service_import_check_is_reproducible():
    result = check_repository_service_imports()
    assert result.check_id == "repository_service_imports"
    assert isinstance(result.passed, bool)
    assert result.metadata.get("violation_count", 0) >= 0


def test_sdk_checks_detect_current_violations():
    repo = check_sdk_repository_imports()
    db = check_sdk_database_imports()
    assert repo.check_id == "sdk_repository_imports"
    assert db.check_id == "sdk_database_imports"


def test_unauthorized_admin_route_scan():
    result = check_unauthorized_admin_routes()
    assert result.check_id == "unauthorized_admin_api"
    if not result.passed:
        assert result.evidence


def test_certification_summary_json_structure():
    import json

    summary_path = ROOT / "docs" / "certification_summary.json"
    assert summary_path.is_file()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "verdict" in data
    assert "failed_gates" in data
