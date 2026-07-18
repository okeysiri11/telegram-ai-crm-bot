#!/usr/bin/env python3
"""Sprint 1.5 — Platform Certification entrypoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_certification.runner import PlatformCertification


def main() -> int:
    result = PlatformCertification(ROOT).run(write_reports=True)
    print(
        f"certification_verdict={result.verdict} "
        f"score={result.overall_score} "
        f"release={result.release_readiness} "
        f"gates={result.gates.pass_count}/{len(result.gates.gates)}"
    )
    if result.manifest_path:
        print(f"manifest={result.manifest_path}")
    for path in result.report_paths:
        print(f"report={path}")
    summary = {
        "verdict": result.verdict,
        "score": result.overall_score,
        "gates_passed": result.gates.pass_count,
        "gates_total": len(result.gates.gates),
        "failed_gates": [
            {"id": g.gate_id, "description": g.description, "evidence": g.evidence}
            for g in result.gates.gates
            if not g.passed
        ],
    }
    out = ROOT / "docs" / "certification_summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
