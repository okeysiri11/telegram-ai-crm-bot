"""Infrastructure smoke tests — Sprint 38.2 recovery guardrails.

Locks in the fixes that made `docker compose up --build` reach a fully healthy
stack: no builtin-shadowing class methods (the `staticmethod is not
subscriptable` class of failure), importable startup-critical modules, and a
compose topology where every service has a healthcheck and the bot applies the
schema before serving.

Live-stack assertions (health endpoints, Postgres/Redis sockets) skip when the
stack is not running, so the suite stays usable in CI.
"""

from __future__ import annotations

import ast
import builtins
import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

SHADOWABLE = {
    name
    for name in ("list", "dict", "set", "tuple", "type", "object", "id", "filter", "map", "input", "any", "all")
    if hasattr(builtins, name)
}

SCANNED_PACKAGES = (
    "services",
    "repositories",
    "platform_jobs",
    "platform_sdk",
    "platform_orchestrator",
    "platform_workflow",
    "platform_enterprise_event_bus",
    "platform_security",
)

CRITICAL_MODULES = (
    "services.commission_engine",
    "services.deal_engine",
    "services.ledger_engine",
    "services.partner_engine",
    "services.ai_router",
    "repositories.partner_repository",
    "platform_jobs.job_engine",
    "platform_sdk.vertical_registry",
    "platform_orchestrator.agent_registry",
    "platform_workflow.registry",
    "platform_enterprise_event_bus.components",
    "platform_security.audit.trail",
)

COMPOSE_SERVICES = ("postgres", "redis", "bot", "nginx", "prometheus", "grafana")


def _iter_python_files():
    for package in SCANNED_PACKAGES:
        yield from (ROOT / package).rglob("*.py")


def _has_future_annotations(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def _annotation_node_ids(class_node: ast.ClassDef) -> set[int]:
    """Every node reachable from an annotation position inside the class."""
    roots: list[ast.AST] = []
    for node in ast.walk(class_node):
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            roots.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                roots.append(node.returns)
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
                if arg is not None and arg.annotation is not None:
                    roots.append(arg.annotation)
    return {id(child) for root in roots for child in ast.walk(root)}


def _shadowing_conflicts(tree: ast.Module) -> list[str]:
    """Class-level defs that shadow a builtin the class body then subscripts.

    With `from __future__ import annotations` the annotations are never
    evaluated, so only subscripts outside annotation positions can blow up at
    import time — that is the failure this guard exists for.
    """
    lazy_annotations = _has_future_annotations(tree)
    conflicts = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        defined = {
            item.name
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in SHADOWABLE
        }
        if not defined:
            continue
        skip = _annotation_node_ids(node) if lazy_annotations else set()
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Subscript)
                and isinstance(inner.value, ast.Name)
                and inner.value.id in defined
                and id(inner) not in skip
            ):
                conflicts.append(f"{node.name}.{inner.value.id}")
    return conflicts


def test_no_builtin_shadowing_in_class_bodies():
    """Regression: `def list(...)` + `-> list[int]` resolved to the staticmethod."""
    offenders: dict[str, list[str]] = {}
    for path in _iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - surfaced by other suites
            continue
        conflicts = _shadowing_conflicts(tree)
        if conflicts:
            offenders[str(path.relative_to(ROOT))] = conflicts
    assert not offenders, f"builtin-shadowing class members reused as subscripts: {offenders}"


def test_renamed_engine_methods_are_present():
    from platform_enterprise_event_bus.components import DeadLetterQueue, EventAuditLogger, EventStore
    from platform_jobs.job_history import JobHistory
    from platform_orchestrator.agent_registry import AgentRegistry
    from platform_sdk.vertical_registry import VerticalRegistry
    from platform_workflow.registry import WorkflowRegistry
    from repositories.partner_repository import PartnerRepository
    from services.commission_engine import CommissionEngine
    from services.deal_engine import DealEngine
    from services.ledger_engine import LedgerEngine
    from services.partner_engine import PartnerEngine

    expected = {
        CommissionEngine: "list_commissions",
        DealEngine: "list_deals",
        LedgerEngine: "list_entries",
        PartnerEngine: "list_partners",
        PartnerRepository: "list_partners",
        JobHistory: "list_entries",
        VerticalRegistry: "list_verticals",
        AgentRegistry: "list_agents",
        WorkflowRegistry: "list_workflows",
        EventStore: "list_events",
        DeadLetterQueue: "list_items",
        EventAuditLogger: "list_entries",
    }
    for cls, method in expected.items():
        assert hasattr(cls, method), f"{cls.__name__}.{method} missing"
        assert not isinstance(vars(cls).get("list"), staticmethod), f"{cls.__name__}.list re-introduced"


@pytest.mark.parametrize("module", CRITICAL_MODULES)
def test_critical_modules_import(module):
    import importlib

    importlib.import_module(module)


def test_audit_trail_records_hash_chain():
    from platform_security.audit.trail import AuditTrail

    trail = AuditTrail()
    first = trail.record(action="user_login", actor="tester")
    second = trail.record(action="api_access", actor="tester")
    assert first["prev_hash"] == "genesis"
    assert second["prev_hash"] == first["entry_hash"]
    assert trail.status() == {"entries": 2, "sealed": False}


def _compose() -> dict:
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))


def test_every_compose_service_declares_a_healthcheck():
    services = _compose()["services"]
    assert set(COMPOSE_SERVICES) <= set(services)
    missing = [name for name in COMPOSE_SERVICES if "healthcheck" not in services[name]]
    assert not missing, f"services without healthcheck: {missing}"


def test_bot_waits_for_healthy_datastores_and_has_start_period():
    bot = _compose()["services"]["bot"]
    depends = bot["depends_on"]
    assert depends["postgres"]["condition"] == "service_healthy"
    assert depends["redis"]["condition"] == "service_healthy"
    # Schema migration runs in the entrypoint; the probe must not fire before it lands.
    assert bot["healthcheck"]["start_period"] == "120s"


def test_entrypoint_applies_schema_before_exec():
    script = (ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")
    lines = [line.strip() for line in script.splitlines() if line.strip() and not line.startswith("#")]
    schema_idx = next(i for i, line in enumerate(lines) if "ensure_local_schema.py" in line)
    exec_idx = next(i for i, line in enumerate(lines) if line.startswith("exec "))
    assert schema_idx < exec_idx


def _http_json(url: str, timeout: float = 5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read()
    except (urllib.error.URLError, OSError) as exc:
        pytest.skip(f"stack not running: {url} ({exc})")


def _tcp(host: str, port: int) -> None:
    try:
        with socket.create_connection((host, port), timeout=3):
            return
    except OSError as exc:
        pytest.skip(f"stack not running: {host}:{port} ({exc})")


@pytest.mark.parametrize("port", [5432, 6379])
def test_datastore_ports_accept_connections(port):
    _tcp("127.0.0.1", port)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080/health",
        "http://127.0.0.1:8080/liveness",
        "http://127.0.0.1:8080/readiness",
        "http://127.0.0.1:8080/ready",
        "http://127.0.0.1:9090/-/healthy",
        "http://127.0.0.1:3000/api/health",
        "http://127.0.0.1/health",
    ],
)
def test_service_health_endpoints_respond(url):
    status, _ = _http_json(url)
    assert status == 200
