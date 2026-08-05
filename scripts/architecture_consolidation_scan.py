#!/usr/bin/env python3
"""Architecture consolidation scan — Sprint 32.3."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if "platform_architecture" not in sys.modules:
        pkg = type(sys)("platform_architecture")
        pkg.__path__ = [str(ROOT / "platform_architecture")]
        sys.modules["platform_architecture"] = pkg

    _load("platform_architecture.canonical_services", ROOT / "platform_architecture/canonical_services.py")
    try:
        _load("platform_architecture.rules", ROOT / "platform_architecture/rules.py")
    except Exception:
        import types

        stub = types.ModuleType("platform_architecture.rules")
        stub.ROOT = ROOT
        sys.modules["platform_architecture.rules"] = stub

    mod = _load(
        "platform_architecture.consolidation_scanner",
        ROOT / "platform_architecture/consolidation_scanner.py",
    )
    report = mod.run_consolidation_scan(ROOT)
    print(f"architecture_consolidation_scan passed={report.passed}")
    for f in report.findings:
        if f.severity in {"critical", "warn"}:
            stream = sys.stderr if f.severity == "critical" else sys.stdout
            print(f"{f.severity.upper()}: [{f.code}] {f.message}", file=stream)
        elif f.code.endswith("_OK") or f.code == "DOC_OK":
            print(f"ok: [{f.code}] {f.message}")
    if "--json" in sys.argv:
        print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
