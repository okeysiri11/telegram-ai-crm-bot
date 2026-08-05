#!/usr/bin/env python3
"""ADOS Sprint 38.3 — Release Candidate smoke pipeline.

Exercises the full local stack end-to-end:

  docker compose down → up --build → health probes → Alembic → Redis → imports

Exit 0 only when every gate passes. Designed for local RC validation and CI.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_MODULES = (
    "services.commission_engine",
    "services.deal_engine",
    "services.ledger_engine",
    "services.partner_engine",
    "services.ai_router",
    "platform_security.audit.trail",
    "platform_jobs.job_engine",
    "platform_sdk.vertical_registry",
    "platform_orchestrator.agent_registry",
    "platform_workflow.registry",
    "startup",
    "bot",
    "api.server",
)

SERVICES = ("postgres", "redis", "bot", "nginx", "prometheus", "grafana")


@dataclass
class Gate:
    name: str
    ok: bool
    detail: str = ""


def _run(cmd: list[str], *, timeout: int = 600, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(cmd)}", flush=True)
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def _http(url: str, *, timeout: float = 8.0) -> tuple[int, bytes]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, response.read()


def _wait_http(url: str, *, expect: int = 200, timeout_s: float = 180.0) -> Gate:
    deadline = time.time() + timeout_s
    last = "no attempt"
    while time.time() < deadline:
        try:
            status, body = _http(url)
            if status == expect:
                return Gate(url, True, f"HTTP {status} ({len(body)} bytes)")
            last = f"HTTP {status}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = str(exc)
        time.sleep(3)
    return Gate(url, False, last)


def _tcp(host: str, port: int) -> Gate:
    try:
        with socket.create_connection((host, port), timeout=5):
            return Gate(f"tcp://{host}:{port}", True, "connected")
    except OSError as exc:
        return Gate(f"tcp://{host}:{port}", False, str(exc))


def _compose_ps_healthy() -> list[Gate]:
    proc = _run(["docker", "compose", "ps", "--format", "json"], check=False)
    gates: list[Gate] = []
    if proc.returncode != 0:
        return [Gate("compose_ps", False, proc.stderr.strip() or proc.stdout.strip())]
    # Compose may emit one JSON object per line or a JSON array.
    raw = proc.stdout.strip()
    rows: list[dict[str, Any]] = []
    if raw.startswith("["):
        rows = json.loads(raw)
    else:
        for line in raw.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    by_service = {row.get("Service") or row.get("Name", ""): row for row in rows}
    for service in SERVICES:
        row = by_service.get(service)
        if not row:
            # container_name may hide Service in some formats — match Name
            row = next(
                (
                    r
                    for r in rows
                    if service in str(r.get("Service", ""))
                    or service in str(r.get("Name", "")).lower()
                ),
                None,
            )
        status = str((row or {}).get("Status") or (row or {}).get("State") or "")
        ok = "healthy" in status.lower()
        gates.append(Gate(f"service:{service}", ok, status or "missing"))
    return gates


def gate_imports() -> list[Gate]:
    # Ensure repo root is importable when invoked outside pytest.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    results = []
    for module in CRITICAL_MODULES:
        try:
            importlib.import_module(module)
            results.append(Gate(f"import:{module}", True))
        except Exception as exc:  # noqa: BLE001 — smoke must surface any failure
            results.append(Gate(f"import:{module}", False, f"{type(exc).__name__}: {exc}"))
    return results


def gate_alembic() -> Gate:
    proc = _run(
        ["docker", "compose", "exec", "-T", "bot", "alembic", "current"],
        timeout=120,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0 and "(head)" in out
    return Gate("alembic_head", ok, out.strip().splitlines()[-1] if out.strip() else "empty")


def gate_redis_ping() -> Gate:
    proc = _run(
        ["docker", "compose", "exec", "-T", "redis", "redis-cli", "ping"],
        timeout=30,
        check=False,
    )
    out = (proc.stdout or "").strip()
    return Gate("redis_ping", out == "PONG", out or proc.stderr.strip())


def gate_postgres() -> Gate:
    proc = _run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            os.environ.get("POSTGRES_USER", "postgres"),
            "-d",
            os.environ.get("POSTGRES_DB", "ai_ecosystem"),
            "-c",
            "SELECT 1;",
        ],
        timeout=30,
        check=False,
    )
    ok = proc.returncode == 0 and "1" in (proc.stdout or "")
    return Gate("postgres_select", ok, (proc.stdout or proc.stderr).strip()[:200])


def run_pipeline(*, rebuild: bool, skip_down: bool) -> int:
    gates: list[Gate] = []

    # Offline gates first — fail fast without touching Docker if imports are broken.
    gates.extend(gate_imports())
    if any(not g.ok for g in gates):
        _print_report(gates)
        return 1

    if not skip_down:
        down = _run(["docker", "compose", "down", "--remove-orphans"], timeout=180, check=False)
        gates.append(Gate("compose_down", down.returncode == 0, down.stderr[-200:] if down.stderr else "ok"))

    up_cmd = ["docker", "compose", "up", "-d"]
    if rebuild:
        up_cmd.insert(3, "--build")
    up = _run(up_cmd, timeout=900, check=False)
    gates.append(Gate("compose_up", up.returncode == 0, (up.stderr or up.stdout)[-300:]))
    if up.returncode != 0:
        _print_report(gates)
        return 1

    # Wait until bot is healthy (migrations + API).
    gates.append(_wait_http("http://127.0.0.1:8080/liveness", timeout_s=240))
    gates.append(_wait_http("http://127.0.0.1:8080/health", timeout_s=120))
    gates.append(_wait_http("http://127.0.0.1:8080/readiness", timeout_s=60))
    gates.append(_wait_http("http://127.0.0.1:8080/ready", timeout_s=60))
    gates.append(_wait_http("http://127.0.0.1:9090/-/healthy", timeout_s=60))
    gates.append(_wait_http("http://127.0.0.1:3000/api/health", timeout_s=90))
    gates.append(_wait_http("http://127.0.0.1/health", timeout_s=60))

    gates.extend(_compose_ps_healthy())
    gates.append(gate_postgres())
    gates.append(gate_redis_ping())
    gates.append(gate_alembic())
    gates.append(_tcp("127.0.0.1", 5432))
    gates.append(_tcp("127.0.0.1", 6379))

    _print_report(gates)
    failed = [g for g in gates if not g.ok]
    return 1 if failed else 0


def _print_report(gates: list[Gate]) -> None:
    print("\n=== SMOKE REPORT (Sprint 38.3) ===")
    for gate in gates:
        mark = "PASS" if gate.ok else "FAIL"
        detail = f" — {gate.detail}" if gate.detail else ""
        print(f"[{mark}] {gate.name}{detail}")
    failed = sum(1 for g in gates if not g.ok)
    print(f"\nTotal: {len(gates)}  PASS: {len(gates) - failed}  FAIL: {failed}")
    report_path = ROOT / "docs" / "smoke_rc_report.json"
    report_path.write_text(
        json.dumps({"gates": [asdict(g) for g in gates], "failed": failed}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-rebuild", action="store_true", help="Skip --build on compose up")
    parser.add_argument("--skip-down", action="store_true", help="Do not tear down first")
    parser.add_argument("--imports-only", action="store_true", help="Only critical imports")
    args = parser.parse_args()
    if args.imports_only:
        gates = gate_imports()
        _print_report(gates)
        return 1 if any(not g.ok for g in gates) else 0
    return run_pipeline(rebuild=not args.no_rebuild, skip_down=args.skip_down)


if __name__ == "__main__":
    raise SystemExit(main())
