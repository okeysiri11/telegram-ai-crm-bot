#!/usr/bin/env python3
"""CI entrypoint — architecture governance validation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_architecture.governance import ArchitectureGovernance


def main() -> int:
    report = ArchitectureGovernance(ROOT).run_all()
    print(
        f"architecture_grade={report.certification.grade.value} "
        f"score={report.certification.architecture_score} "
        f"passed={report.passed}"
    )
    if report.report_path:
        print(f"report={report.report_path}")
    if report.certificate_path:
        print(f"certificate={report.certificate_path}")
    if not report.passed:
        for failure in report.certification.gate_failures:
            print(f"gate_failure: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
