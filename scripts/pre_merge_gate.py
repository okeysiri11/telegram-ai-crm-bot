#!/usr/bin/env python3
"""Mandatory pre-merge gate — Sprint 38.4 Safe Development Policy.

Runs the checks that must be green before a sprint/PR is considered complete:

  1. Ruff (critical)
  2. Platform protections
  3. Pytest RC suite
  4. Optional live smoke (compose + /health + /ready) when --with-docker is set

Usage:
  python scripts/pre_merge_gate.py
  python scripts/pre_merge_gate.py --with-docker
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, timeout: int = 900) -> int:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, timeout=timeout)
    print(f"<<< exit={proc.returncode}", flush=True)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Also run full compose smoke (health/ready/containers).",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip RC pytest (not allowed for merge; local iterate only).",
    )
    args = parser.parse_args()
    py = sys.executable
    steps: list[tuple[str, list[str]]] = [
        (
            "ruff",
            [
                py,
                "-m",
                "ruff",
                "check",
                "services",
                "repositories",
                "platform_security",
                "platform_jobs",
                "platform_sdk",
                "api",
                "scripts/validate_platform_protections.py",
                "scripts/pre_merge_gate.py",
                "scripts/smoke_platform_rc.py",
                "--select",
                "E9,F63,F7,F82",
            ],
        ),
        ("protections", [py, "scripts/validate_platform_protections.py"]),
    ]
    if not args.skip_pytest:
        steps.append(("pytest_rc", [py, "scripts/run_rc_test_suite.py"]))
    if args.with_docker:
        steps.append(
            (
                "smoke_docker",
                [py, "scripts/smoke_platform_rc.py", "--skip-down", "--no-rebuild"],
            )
        )

    failed: list[str] = []
    for name, cmd in steps:
        # Ensure ruff is available
        if name == "ruff":
            try:
                import ruff  # noqa: F401
            except ImportError:
                subprocess.run([py, "-m", "pip", "install", "-q", "ruff==0.9.10"], cwd=ROOT, check=False)
        code = _run(cmd)
        if code != 0:
            failed.append(name)

    print("\n=== PRE-MERGE GATE SUMMARY ===")
    if failed:
        print("FAILED:", ", ".join(failed))
        print("Sprint/PR incomplete per docs/DEVELOPMENT_POLICY.md")
        return 1
    print("ALL REQUIRED GATES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
