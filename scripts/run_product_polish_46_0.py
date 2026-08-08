#!/usr/bin/env python3
"""Epic 46.0 — run product polish audit + enterprise certification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from platform_product.certification import enterprise_certification  # noqa: E402


def main() -> int:
    report = enterprise_certification.run()
    out = ROOT / "docs" / "ENTERPRISE_CERTIFICATION_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ROOT / "docs" / "ENTERPRISE_CERTIFICATION.md"
    lines = [
        "# Enterprise Certification",
        "",
        f"**Overall:** {report['overall']}",
        f"**Version:** {report['version']}",
        "",
        "| Area | Status |",
        "|------|--------|",
    ]
    for a in report["areas"]:
        lines.append(f"| {a['area']} | {a['status']} |")
    lines.extend(["", f"Audit passed: {report['audit']['passed']}/{report['audit']['total']}", ""])
    md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "ready": report["ready"]}, ensure_ascii=False))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
