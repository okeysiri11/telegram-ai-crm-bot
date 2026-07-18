#!/usr/bin/env python3
"""CI entrypoint — validate legacy migration boundaries."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_legacy.ci_validation import assert_legacy_ci_clean
from platform_legacy.docs_generator import write_legacy_migration_doc


def main() -> int:
    assert_legacy_ci_clean()
    path = write_legacy_migration_doc()
    print(f"legacy_ci_ok doc={path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
