#!/usr/bin/env python3
"""Fail CI when Telegram handlers import get_session directly."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.platform.layers.session_policy import scan_handler_session_violations


def main() -> int:
    violations = scan_handler_session_violations(ROOT)
    if not violations:
        print("OK: no handler session violations")
        return 0
    print("Handler session policy violations:")
    for path in violations:
        print(f"  - {path}")
    print("\nHandlers must call services instead of get_session().")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
