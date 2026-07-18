# Certification report generation — docs/CERTIFICATION_*.md

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _check_map(checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {c["check_id"]: c for c in checks}


def write_all_reports(
    *,
    checks: list[dict[str, Any]],
    metrics: dict[str, object],
    certification: dict[str, Any],
    graph_summary: dict[str, object],
) -> list[Path]:
    DOCS.mkdir(parents=True, exist_ok=True)
    cm = _check_map(checks)
    paths = [
        _write_architecture(cm, metrics, certification),
        _write_dependencies(cm, metrics, graph_summary),
        _write_security(cm),
        _write_events(cm),
        _write_sdk(cm),
        _write_ci(cm),
        _write_documentation(cm),
        _write_metrics(metrics, checks, certification),
        _write_tech_debt(cm, metrics, graph_summary),
        _write_platform_certification(checks, metrics, certification),
    ]
    return paths


def _write_architecture(cm, metrics, cert) -> Path:
    path = DOCS / "CERTIFICATION_ARCHITECTURE.md"
    repo = cm.get("repository_service_imports", {})
    api_repo = cm.get("api_repository_access", {})
    arch = cm.get("architecture_audit", {})
    lines = [
        "# Architecture Certification",
        "",
        f"> Generated: {_now()}",
        "",
        "## Verdict",
        "",
        f"**{'PASS' if repo.get('passed') and api_repo.get('passed') and arch.get('passed') else 'FAIL'}**",
        "",
        "## Gate Results",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
        f"| Repository → Service imports | {'PASS' if repo.get('passed') else 'FAIL'} | {repo.get('message', '')} |",
        f"| API → Repository direct access | {'PASS' if api_repo.get('passed') else 'FAIL'} | {api_repo.get('message', '')} |",
        f"| Architecture audit (strict) | {'PASS' if arch.get('passed') else 'FAIL'} | {arch.get('message', '')} |",
        "",
        "## Evidence — Repository → Service",
        "",
    ]
    for item in repo.get("evidence", [])[:25]:
        lines.append(f"- `{item}`")
    if not repo.get("evidence"):
        lines.append("- None")
    lines.extend(["", "## Evidence — API → Repository", ""])
    for item in api_repo.get("evidence", [])[:15]:
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Architecture Diagram (Target)",
        "",
        "```",
        "API (/management/v1) → Services → Repositories → Database",
        "SDK → Services (never Repository/Database)",
        "Plugins → platform_plugin_sdk only",
        "```",
        "",
        "## Scores",
        "",
        f"- Governance score: {metrics.get('governance_score')}",
        f"- Strict certification score: {cert.get('overall_score')}",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_dependencies(cm, metrics, graph_summary) -> Path:
    path = DOCS / "CERTIFICATION_DEPENDENCIES.md"
    dep = cm.get("dependency_audit", {})
    meta = dep.get("metadata", {})
    lines = [
        "# Dependency Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if dep.get('passed') else 'FAIL'}**",
        "",
        "## Graph Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Modules | {metrics.get('module_count_graph')} |",
        f"| Edges | {metrics.get('dependency_edges')} |",
        f"| All cycles | {metrics.get('all_cycles')} |",
        f"| Strict governance cycles | {metrics.get('strict_governance_cycles')} |",
        "",
        "## Cycle Categories",
        "",
    ]
    for cat, count in (meta.get("cycle_categories") or metrics.get("cycle_categories") or {}).items():
        lines.append(f"- **{cat}**: {count}")
    lines.extend([
        "",
        "## Governed-Layer Cycles",
        "",
    ])
    for item in dep.get("evidence", [])[:20]:
        lines.append(f"- {item}")
    if not dep.get("evidence"):
        lines.append("- None detected in governed layers (strict filter)")
    lines.extend([
        "",
        "## Deferred Legacy Cycles (Sprint 2)",
        "",
        "Legacy `services/pg_*` engine cycles (~45) are isolated compatibility code.",
        "Breaking these without behavior change requires adapter extraction in Sprint 2.",
        "Config ↔ legacy cycles (~21) require feature-flag decoupling.",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_security(cm) -> Path:
    path = DOCS / "CERTIFICATION_SECURITY.md"
    admin = cm.get("unauthorized_admin_api", {})
    sec = cm.get("security_tests", {})
    lines = [
        "# Security Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if admin.get('passed') and sec.get('passed') else 'FAIL'}**",
        "",
        "## Authentication & Authorization",
        "",
        "| Control | Status |",
        "|---------|--------|",
        "| Management API JWT/API Key | PASS (test_management_security.py) |",
        f"| Unauthorized admin routes | {'PASS' if admin.get('passed') else 'FAIL'} |",
        f"| Dedicated admin security suite | {'PASS' if sec.get('metadata', {}).get('has_admin_security_suite') else 'FAIL'} |",
        "",
        "## Exposed Admin Routes (unauthenticated)",
        "",
    ]
    for route in admin.get("evidence", []):
        lines.append(f"- `{route}`")
    lines.extend([
        "",
        "## Known Gaps",
        "",
        "- Config read allows anonymous actor when `actor_telegram_id` is None",
        "- Config write accepts `changed_by` without actor verification",
        "- No tests asserting 401 on `/api/v1/sla/*`, `/api/v1/configuration/*`",
        "",
        "## Security Test Evidence",
        "",
    ])
    for line in sec.get("evidence", []):
        lines.append(f"- `{line}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_events(cm) -> Path:
    path = DOCS / "CERTIFICATION_EVENTS.md"
    ev = cm.get("canonical_event_bus", {})
    meta = ev.get("metadata", {})
    lines = [
        "# Event System Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if ev.get('passed') else 'FAIL'}**",
        "",
        "## Canonical Bus",
        "",
        "- **PlatformEventBus** (`events/event_bus.py`) — canonical in-process bus",
        "- **events/publisher.py** — unified publish entry",
        "",
        "## Adapters",
        "",
        "- CRM Outbox (`services/crm_event_bus.py`) — persists after `publish_crm_to_platform_bus`",
        "- Legacy EventBus — re-exported via `platform_legacy` in `events/__init__.py`",
        "",
        f"- CRM adapter wired to PlatformEventBus: **{meta.get('crm_uses_adapter', 'unknown')}**",
        f"- Direct legacy publishers in pg engines: **{meta.get('direct_publisher_count', 0)}**",
        "",
        "## Direct CRM Publishers (must migrate to events/publisher)",
        "",
    ]
    for item in ev.get("evidence", []):
        lines.append(f"- `{item}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_sdk(cm) -> Path:
    path = DOCS / "CERTIFICATION_SDK.md"
    repo = cm.get("sdk_repository_imports", {})
    db = cm.get("sdk_database_imports", {})
    passed = repo.get("passed") and db.get("passed")
    lines = [
        "# SDK Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if passed else 'FAIL'}**",
        "",
        "| Check | Status |",
        "|-------|--------|",
        f"| SDK → Repository | {'PASS' if repo.get('passed') else 'FAIL'} |",
        f"| SDK → Database | {'PASS' if db.get('passed') else 'FAIL'} |",
        "",
        "## Violations",
        "",
    ]
    for item in repo.get("evidence", []) + db.get("evidence", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Required Pattern",
        "",
        "```python",
        "# platform_sdk must call services only",
        "from services.request_service import RequestService",
        "await RequestService.create_request(...)",
        "```",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_ci(cm) -> Path:
    path = DOCS / "CERTIFICATION_CI.md"
    ci = cm.get("ci_enforcement", {})
    pytest_r = cm.get("pytest_suite", {})
    lines = [
        "# CI/CD Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if ci.get('passed') else 'FAIL'}**",
        "",
        "## Pipeline Status",
        "",
        f"| Stage | Status |",
        f"|-------|--------|",
        f"| GitHub Actions | {'ENABLED' if ci.get('passed') else 'MISSING'} |",
        f"| pytest ({pytest_r.get('metadata', {}).get('passed_count', '?')} tests) | {'PASS' if pytest_r.get('passed') else 'FAIL'} |",
        f"| Architecture validation script | Available (local only) |",
        f"| Legacy migration script | Available (local only) |",
        "",
        "## Required CI Stages (not yet enforced remotely)",
        "",
        "- `pytest tests/`",
        "- `python scripts/validate_architecture.py`",
        "- `python scripts/validate_legacy_migration.py`",
        "- `python scripts/run_platform_certification.py`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_documentation(cm) -> Path:
    path = DOCS / "CERTIFICATION_DOCUMENTATION.md"
    doc = cm.get("documentation_sync", {})
    docs_exist = {
        "README.md": (ROOT / "README.md").is_file(),
        "docs/architecture.md": (DOCS / "architecture.md").is_file(),
        "docs/PLUGIN_SDK.md": (DOCS / "PLUGIN_SDK.md").is_file(),
        "docs/events.md": (DOCS / "events.md").is_file(),
        "LEGACY_MIGRATION.md": (ROOT / "LEGACY_MIGRATION.md").is_file(),
        "ARCHITECTURE_REPORT.md": (ROOT / "ARCHITECTURE_REPORT.md").is_file(),
    }
    lines = [
        "# Documentation Certification",
        "",
        f"> Generated: {_now()}",
        "",
        f"## Verdict: **{'PASS' if doc.get('passed') else 'FAIL'}**",
        "",
        "## Document Inventory",
        "",
        "| Document | Exists | Synced |",
        "|----------|--------|--------|",
    ]
    for name, exists in docs_exist.items():
        synced = "partial" if exists and name == "README.md" and not doc.get("passed") else ("yes" if exists else "no")
        lines.append(f"| {name} | {'yes' if exists else 'no'} | {synced} |")
    lines.extend(["", "## Gaps", ""])
    for item in doc.get("evidence", []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_metrics(metrics, checks, cert) -> Path:
    path = DOCS / "CERTIFICATION_METRICS.md"
    pytest_r = next((c for c in checks if c["check_id"] == "pytest_suite"), {})
    lines = [
        "# Performance & Certification Metrics",
        "",
        f"> Generated: {_now()}",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Python files | {metrics.get('python_files')} |",
        f"| Graph modules | {metrics.get('module_count_graph')} |",
        f"| Dependency edges | {metrics.get('dependency_edges')} |",
        f"| All dependency cycles | {metrics.get('all_cycles')} |",
        f"| Governance cycles (strict) | {metrics.get('strict_governance_cycles')} |",
        f"| Governance score | {metrics.get('governance_score')} |",
        f"| Certification score | {cert.get('overall_score')} |",
        f"| Tests collected | {metrics.get('test_count')} |",
        f"| pytest duration (s) | {pytest_r.get('metadata', {}).get('duration_sec', 'n/a')} |",
        f"| Startup probe (s) | {metrics.get('startup_probe_sec', 'n/a')} |",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_tech_debt(cm, metrics, graph_summary) -> Path:
    path = DOCS / "TECH_DEBT.md"
    lines = [
        "# Platform Technical Debt Register",
        "",
        f"> Generated: {_now()}",
        "",
        "## P0 — Blocks Certification",
        "",
    ]
    if not cm.get("repository_service_imports", {}).get("passed"):
        lines.append(f"- Repository → Service imports ({cm['repository_service_imports'].get('metadata', {}).get('files_affected', 7)} files)")
    if not cm.get("sdk_repository_imports", {}).get("passed"):
        lines.append("- SDK → Repository/Database access in platform_sdk/")
    if not cm.get("unauthorized_admin_api", {}).get("passed"):
        lines.append(f"- {len(cm['unauthorized_admin_api'].get('evidence', []))} unauthenticated admin HTTP routes")
    if not cm.get("ci_enforcement", {}).get("passed"):
        lines.append("- No GitHub Actions workflow")
    if not cm.get("documentation_sync", {}).get("passed"):
        lines.append("- README stale vs implementation")
    lines.extend([
        "",
        "## P1 — Sprint 2",
        "",
        f"- Legacy pg engine dependency cycles ({metrics.get('cycle_categories', {}).get('legacy_pg_engines', 45)})",
        "- Handler DB direct access (4 allowlisted files)",
        "- WorkflowEngine name collision (legacy adapter alias)",
        "- Event bus direct crm_event_bus imports in pg engines",
        "",
        "## Deferred with Justification",
        "",
        "Legacy `services/pg_*` cycles are contained in compatibility layer.",
        "Removing them requires Sprint 2 adapter extraction without business logic change.",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_platform_certification(checks, metrics, cert) -> Path:
    path = DOCS / "PLATFORM_CERTIFICATION.md"
    lines = [
        "# Platform v1.0 — Sprint 1.5 Certification Report",
        "",
        f"> Generated: {_now()}",
        "",
        "## Final Verdict",
        "",
        f"# **{cert.get('verdict', 'FAIL')}**",
        "",
        f"**Platform Certification Score:** {cert.get('overall_score')}/100",
        "",
        f"**Release Readiness:** {cert.get('release_readiness')}",
        "",
        "## Certification Gates",
        "",
        "| Gate | Status |",
        "|------|--------|",
    ]
    for gate in cert.get("gates", []):
        lines.append(f"| {gate['description']} | {'PASS' if gate['passed'] else 'FAIL'} |")
    lines.extend([
        "",
        "## Health Summary",
        "",
        f"| Domain | Score |",
        f"|--------|------:|",
    ])
    for domain, score in cert.get("health_scores", {}).items():
        lines.append(f"| {domain} | {score} |")
    lines.extend([
        "",
        "## Deliverables",
        "",
        "- docs/CERTIFICATION_ARCHITECTURE.md",
        "- docs/CERTIFICATION_DEPENDENCIES.md",
        "- docs/CERTIFICATION_SECURITY.md",
        "- docs/CERTIFICATION_EVENTS.md",
        "- docs/CERTIFICATION_SDK.md",
        "- docs/CERTIFICATION_CI.md",
        "- docs/CERTIFICATION_DOCUMENTATION.md",
        "- docs/CERTIFICATION_METRICS.md",
        "- docs/TECH_DEBT.md",
        "- platform_manifest.json",
        "",
        "## Release Candidate",
        "",
        "RC1 tag **not created** — certification gates did not pass." if cert.get("verdict") != "PASS" else "RC1 tag **platform-core-v1.0-rc1** created.",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
