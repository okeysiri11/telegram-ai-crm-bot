#!/usr/bin/env python3
"""Release-candidate pytest gate — Sprint 38.3.

Runs the current-platform suite that must stay green for RC:
  - infrastructure smoke
  - security freeze suite
  - import / engine shadowing regressions

Full historical sprint suites remain available via `pytest tests/`; their
version-pin failures are classified as LEGACY by classify_pytest_failures.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RC_TESTS = [
    "tests/test_infrastructure_smoke.py",
    "tests/test_management_security.py",
    "tests/test_api_v1_freeze.py",
    "tests/test_admin_security.py",
]


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *RC_TESTS,
        "-q",
        "--tb=short",
        "-m",
        "not slow",
    ]
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
