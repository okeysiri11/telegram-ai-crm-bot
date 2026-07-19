# Certification checks — reproducible automated verification.

from __future__ import annotations

import ast
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPO_SERVICE_PATTERN = re.compile(r"^\s*(from services\.|import services\.)")
SDK_ROOT = ROOT / "platform_sdk"
ADMIN_ROUTE_PATTERN = re.compile(
    r"register_(?:sla|managers_pool|assignment|workflow|platform_sdk|configuration)_admin_routes\(app\)"
)


@dataclass
class CheckResult:
    check_id: str
    passed: bool
    message: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


def _python_files(base: Path) -> list[Path]:
    skip = {".venv", "venv", "node_modules", "__pycache__", ".git"}
    files: list[Path] = []
    for path in base.rglob("*.py"):
        if any(part in skip for part in path.parts):
            continue
        files.append(path)
    return files


def check_repository_service_imports() -> CheckResult:
    violations: list[str] = []
    repo_root = ROOT / "repositories"
    for path in _python_files(repo_root):
        rel = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if REPO_SERVICE_PATTERN.match(line):
                violations.append(f"{rel}:{line_no}: {line.strip()}")
    return CheckResult(
        check_id="repository_service_imports",
        passed=not violations,
        message=f"{len(violations)} Repository → Service import(s)",
        evidence=violations,
        metadata={"violation_count": len(violations), "files_affected": len({v.split(":")[0] for v in violations})},
    )


def check_sdk_repository_imports() -> CheckResult:
    violations: list[str] = []
    if not SDK_ROOT.is_dir():
        return CheckResult("sdk_repository_imports", False, "platform_sdk/ missing", [])
    for path in _python_files(SDK_ROOT):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
            if mod and (mod == "repositories" or mod.startswith("repositories.")):
                violations.append(f"{rel}:{node.lineno}: imports {mod}")
    return CheckResult(
        check_id="sdk_repository_imports",
        passed=not violations,
        message=f"{len(violations)} SDK → Repository import(s)",
        evidence=violations,
    )


def check_sdk_database_imports() -> CheckResult:
    violations: list[str] = []
    forbidden = ("database", "database.session", "database.models", "get_session")
    for path in _python_files(SDK_ROOT):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "database" or node.module.startswith("database."):
                    violations.append(f"{rel}:{node.lineno}: imports {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "database" or alias.name.startswith("database."):
                        violations.append(f"{rel}:{node.lineno}: imports {alias.name}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "get_session" in text:
            for line_no, line in enumerate(text.splitlines(), 1):
                if "get_session" in line and not line.strip().startswith("#"):
                    violations.append(f"{rel}:{line_no}: uses get_session")
    return CheckResult(
        check_id="sdk_database_imports",
        passed=not violations,
        message=f"{len(violations)} SDK → Database access point(s)",
        evidence=sorted(set(violations)),
    )


def check_unauthorized_admin_routes() -> CheckResult:
    server = ROOT / "api" / "server.py"
    text = server.read_text(encoding="utf-8")
    registrations = ADMIN_ROUTE_PATTERN.findall(text)
    admin_routes: list[str] = []
    for router_file in (ROOT / "routers" / "admin").glob("*.py"):
        if router_file.name == "__init__.py":
            continue
        content = router_file.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'add_(get|post|put|delete|patch)\("([^"]+)"', content):
            admin_routes.append(f"{match.group(1).upper()} {match.group(2)} ({router_file.name})")
    return CheckResult(
        check_id="unauthorized_admin_api",
        passed=not registrations,
        message=f"{len(registrations)} admin route registration call(s) in api/server.py",
        evidence=admin_routes,
        metadata={"registration_calls": registrations},
    )


def check_ci_enforcement() -> CheckResult:
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml")) + list(
        (ROOT / ".github" / "workflows").glob("*.yaml")
    )
    has_arch = any("architecture" in w.name.lower() or "ci" in w.name.lower() for w in workflows)
    return CheckResult(
        check_id="ci_enforcement",
        passed=bool(workflows) and has_arch,
        message=f"{len(workflows)} workflow file(s) under .github/workflows",
        evidence=[w.relative_to(ROOT).as_posix() for w in workflows],
    )


def check_documentation_sync() -> CheckResult:
    readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="ignore")
    markers = (
        "platform_management",
        "platform_architecture",
        "PlatformEventBus",
        "platform_plugin_sdk",
        "/management/v1",
    )
    missing = [m for m in markers if m not in readme]
    stale = "bot.py" in readme and "startup.py" not in readme
    passed = not missing and not stale
    evidence = [f"missing marker: {m}" for m in missing]
    if stale:
        evidence.append("README still describes bot.py-only layout (stale)")
    return CheckResult(
        check_id="documentation_sync",
        passed=passed,
        message="README reflects current platform" if passed else "README out of sync",
        evidence=evidence,
    )


def check_architecture_audit() -> CheckResult:
    from platform_architecture.governance import ArchitectureGovernance
    from platform_architecture.rules import ViolationSeverity

    report = ArchitectureGovernance(ROOT).run_all(write_reports=False)
    critical = report.critical_violations
    strict_score = _compute_strict_architecture_score(report, critical)
    return CheckResult(
        check_id="architecture_audit",
        passed=report.passed and strict_score >= 95 and not critical,
        message=f"governance={report.certification.grade.value} score={report.certification.architecture_score} strict={strict_score}",
        evidence=[f"[{v.category}/{v.rule}] {v.path}: {v.detail}" for v in critical[:30]],
        metadata={
            "governance_score": report.certification.architecture_score,
            "strict_score": strict_score,
            "critical_count": len(critical),
            "gate_failures": report.certification.gate_failures,
        },
    )


def _compute_strict_architecture_score(report, critical: list) -> float:
    score = float(report.certification.architecture_score)
    score -= len(critical) * 5
    for failure in report.certification.gate_failures:
        if "cycle" in failure.lower() or "violation" in failure.lower():
            score -= 10
    return max(0.0, round(score, 2))


def check_dependency_audit() -> CheckResult:
    from platform_architecture.dependency_graph import build_dependency_graph
    from platform_architecture.import_scanner import scan_all_imports, critical_import_violations

    graph = build_dependency_graph(ROOT)
    all_cycles = _all_cycles(graph)
    strict_cycles = graph.cycles
    imports = critical_import_violations(scan_all_imports(ROOT))
    passed = not strict_cycles and not imports
    return CheckResult(
        check_id="dependency_audit",
        passed=passed,
        message=(
            f"strict_cycles={len(strict_cycles)} all_cycles={len(all_cycles)} "
            f"import_critical={len(imports)}"
        ),
        evidence=[f"cycle: {' -> '.join(c[:8])}" for c in strict_cycles[:15]],
        metadata={
            "all_cycles": len(all_cycles),
            "governed_cycles": len(strict_cycles),
            "strict_governance_cycles": len(graph.cycles),
            "nodes": graph.node_count,
            "edges": graph.edge_count,
            "cycle_categories": dict(_categorize_cycles(all_cycles, graph)),
        },
    )


def _all_cycles(graph) -> list[list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for src, dst in graph.edges:
        adj[src].append(dst)
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        stack.add(node)
        path.append(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in stack:
                idx = path.index(neighbor)
                cycle = path[idx:] + [neighbor]
                if cycle not in cycles and len(cycle) > 2:
                    cycles.append(cycle)
        path.pop()
        stack.remove(node)

    for node in sorted(graph.nodes):
        if node not in visited:
            dfs(node)
    return cycles


def _cycle_touches_governed(cycle: list[str], graph) -> bool:
    from platform_architecture.rules import GOVERNED_LAYERS

    for node in cycle:
        if node in graph.nodes and graph.nodes[node].layer in GOVERNED_LAYERS:
            return True
    return False


def _categorize_cycles(cycles: list[list[str]], graph) -> Counter[str]:
    cats: Counter[str] = Counter()
    for cycle in cycles:
        s = ".".join(cycle)
        if "database.models" in s:
            cats["orm_models"] += 1
        elif "services.pg_" in s:
            cats["legacy_pg_engines"] += 1
        elif "platform_legacy" in s or "platform_configuration" in s:
            cats["config_legacy"] += 1
        elif "platform_identity" in s or "platform_management" in s:
            cats["platform_core"] += 1
        else:
            cats["other"] += 1
    return cats


def check_canonical_event_bus() -> CheckResult:
    direct_crm = []
    crm_root = ROOT / "services" / "crm_event_bus.py"
    for path in _python_files(ROOT / "services"):
        if path.name == "crm_event_bus.py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("services/pg_"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "crm_event_bus" in text:
                direct_crm.append(rel)
    publisher_exists = (ROOT / "events" / "publisher.py").is_file()
    crm_uses_adapter = "publish_crm_to_platform_bus" in crm_root.read_text(encoding="utf-8")
    legacy_reexport = "EventBus = legacy" in (ROOT / "events" / "__init__.py").read_text(encoding="utf-8")
    passed = publisher_exists and crm_uses_adapter and len(direct_crm) <= 17
    return CheckResult(
        check_id="canonical_event_bus",
        passed=publisher_exists and crm_uses_adapter and not direct_crm,
        message=f"direct_crm_publishers={len(direct_crm)} adapter_wired={crm_uses_adapter}",
        evidence=direct_crm[:20],
        metadata={"legacy_eventbus_reexport": legacy_reexport, "direct_publisher_count": len(direct_crm)},
    )


def check_security_tests() -> CheckResult:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_management_security.py",
        "tests/test_api_v1_freeze.py",
        "tests/test_admin_security.py",
        "-q",
        "--tb=no",
    ]
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    duration = time.perf_counter() - start
    passed = proc.returncode == 0
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
    admin_security_test = (ROOT / "tests" / "test_admin_security.py").is_file()
    return CheckResult(
        check_id="security_tests",
        passed=passed and admin_security_test,
        message=f"pytest security exit={proc.returncode} admin_security_test={admin_security_test}",
        evidence=tail,
        metadata={"duration_sec": round(duration, 2), "has_admin_security_suite": admin_security_test},
    )


def check_api_repository_access() -> CheckResult:
    api_paths = [
        ROOT / "platform_management",
        ROOT / "platform_api",
        ROOT / "api",
        ROOT / "routers",
    ]
    violations: list[str] = []
    for base in api_paths:
        if not base.is_dir():
            continue
        for path in _python_files(base):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("repositories."):
                        violations.append(f"{rel}:{node.lineno}: {node.module}")
    return CheckResult(
        check_id="api_repository_access",
        passed=not violations,
        message=f"{len(violations)} API → Repository direct import(s)",
        evidence=violations,
    )


def run_pytest_suite() -> CheckResult:
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "-m", "not slow"]
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    duration = time.perf_counter() - start
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    summary = lines[-1] if lines else "no output"
    count_match = re.search(r"(\d+) passed", summary)
    return CheckResult(
        check_id="pytest_suite",
        passed=proc.returncode == 0,
        message=summary,
        evidence=lines[-5:],
        metadata={"duration_sec": round(duration, 2), "passed_count": int(count_match.group(1)) if count_match else 0},
    )


def collect_metrics() -> dict[str, object]:
    from platform_architecture.dependency_graph import build_dependency_graph
    from platform_architecture.governance import ArchitectureGovernance

    graph = build_dependency_graph(ROOT)
    all_cycles = _all_cycles(graph)
    gov = ArchitectureGovernance(ROOT).run_all(write_reports=False)

    startup_sec: float | None = None
    try:
        start = time.perf_counter()
        from platform_architecture.api_validator import validate_api

        validate_api(ROOT)
        startup_sec = round(time.perf_counter() - start, 3)
    except Exception:
        startup_sec = None

    test_collect = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    collect_line = test_collect.stdout.strip().splitlines()[-1] if test_collect.stdout else ""
    test_count_match = re.search(r"(\d+) tests collected", collect_line)

    py_files = len(list(ROOT.rglob("*.py")))
    return {
        "module_count_graph": graph.node_count,
        "dependency_edges": graph.edge_count,
        "all_cycles": len(all_cycles),
        "strict_governance_cycles": len(graph.cycles),
        "governance_score": gov.certification.architecture_score,
        "governance_grade": gov.certification.grade.value,
        "startup_probe_sec": startup_sec,
        "test_count": int(test_count_match.group(1)) if test_count_match else 0,
        "python_files": py_files,
        "cycle_categories": dict(_categorize_cycles(all_cycles, graph)),
    }
