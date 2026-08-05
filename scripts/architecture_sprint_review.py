#!/usr/bin/env python3
"""Sprint architecture review — duplicates, ownership, compatibility (Sprint 32.2)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_sprint_review():
    """Load sprint_review without importing platform_architecture.__init__ (heavy deps)."""
    # Ensure a lightweight package stub exists for absolute imports inside modules.
    if "platform_architecture" not in sys.modules:
        pkg = type(sys)("platform_architecture")
        pkg.__path__ = [str(ROOT / "platform_architecture")]
        sys.modules["platform_architecture"] = pkg

    _load_module(
        "platform_architecture.core_inventory",
        ROOT / "platform_architecture" / "core_inventory.py",
    )
    # rules.py may pull more; only needed for ROOT — load carefully.
    rules_path = ROOT / "platform_architecture" / "rules.py"
    try:
        _load_module("platform_architecture.rules", rules_path)
    except Exception:
        # Fallback: inject minimal ROOT for sprint_review
        import types

        rules_stub = types.ModuleType("platform_architecture.rules")
        rules_stub.ROOT = ROOT
        sys.modules["platform_architecture.rules"] = rules_stub

    return _load_module(
        "platform_architecture.sprint_review",
        ROOT / "platform_architecture" / "sprint_review.py",
    )


def main() -> int:
    mod = _load_sprint_review()
    report = mod.run_sprint_architecture_review(ROOT)
    print(f"sprint_architecture_review passed={report.passed}")
    for f in report.findings:
        if f.severity in {"critical", "warn"}:
            stream = sys.stderr if f.severity == "critical" else sys.stdout
            print(f"{f.severity.upper()}: [{f.code}] {f.message}", file=stream)
        elif f.severity == "info" and f.code.endswith("_OK"):
            print(f"ok: [{f.code}] {f.message}")
    if "--json" in sys.argv:
        print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
