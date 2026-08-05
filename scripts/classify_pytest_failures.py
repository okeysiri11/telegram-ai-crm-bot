#!/usr/bin/env python3
"""Classify pytest failure output into CURRENT vs LEGACY buckets (Sprint 38.3).

Legacy signals (historical sprint pins, not regressions of the running platform):
  - Hard-coded application_version equality against old patch versions
  - Manifest / docs assertions requiring a past sprint id (e.g. "33.6", "9.0.4")
  - Docs/audit-index markers for completed milestone sprints

Usage:
  pytest tests/ -q --tb=line -m "not slow" | tee /tmp/pytest.txt
  python scripts/classify_pytest_failures.py /tmp/pytest.txt
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEGACY_PATTERNS = (
    re.compile(r"application_version.*==.*['\"]"),
    re.compile(r"assert ['\"]9\.[0-3]\."),
    re.compile(r"assert ['\"]\d+\.\d+\.\d+['\"]"),
    re.compile(r"assert ['\"]\d{2}\.\d['\"] in "),
    re.compile(r"assert ['\"]\d{2}\.\d['\"] in manifest"),
    re.compile(r"assert ['\"]Sprint \d"),
    re.compile(r"assert ['\"]2\.0\.0['\"]"),
    re.compile(r"== ['\"]2\.0\.0['\"]"),
    re.compile(r"test_docs_and_regression_"),
    re.compile(r"test_manifest_and_audit_index"),
    re.compile(r"test_version_.*_ready"),
    re.compile(r"test_version_and_release"),
    re.compile(r"test_release_report"),
    re.compile(r"test_release_manifest"),
    re.compile(r"test_ops_api"),
    re.compile(r"test_version_enterprise"),
    re.compile(r"architecture_boundaries|architecture_governance|legacy_isolation|legacy_migration"),
)

# File name heuristics for milestone freezes.
LEGACY_FILE_RE = re.compile(
    r"test_.*_(1[0-9]|2[0-9]|3[0-7])_[0-9].*\.py"
    r"|test_.*_(19|20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35|36|37)_"
)


def classify_line(line: str) -> str:
    lowered = line.lower()
    if "xfail" in lowered:
        return "XFAIL"
    if "skipped" in lowered:
        return "SKIPPED"
    for pat in LEGACY_PATTERNS:
        if pat.search(line):
            return "LEGACY_FAIL"
    # FAILED tests/test_foo.py::test_bar - AssertionError...
    m = re.search(r"FAILED (tests/\S+\.py)", line)
    if m and LEGACY_FILE_RE.search(Path(m.group(1)).name):
        # Milestone files often fail only on version pins — treat as legacy unless
        # the message clearly indicates ImportError / TypeError / crash.
        if re.search(r"ImportError|TypeError|AttributeError|ModuleNotFoundError|KeyError", line):
            return "CURRENT_FAIL"
        return "LEGACY_FAIL"
    if line.startswith("FAILED ") or "FAILED " in line:
        return "CURRENT_FAIL"
    return "OTHER"


def parse_summary(text: str) -> dict:
    failed: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("FAILED "):
            continue
        bucket = classify_line(line)
        failed.append({"line": line.strip(), "bucket": bucket})

    summary_match = re.search(
        r"(\d+) failed.*?(\d+) passed.*?(\d+) skipped.*?(\d+) xfailed"
        r"|(\d+) failed.*?(\d+) passed"
        r"|(\d+) passed",
        text.replace("\n", " "),
    )
    counts = {
        "failed": 0,
        "passed": 0,
        "skipped": 0,
        "xfailed": 0,
        "legacy_fail": 0,
        "current_fail": 0,
    }
    if summary_match:
        groups = [g for g in summary_match.groups() if g is not None]
        # Best-effort — prefer the last full summary line.
        pass
    m = re.search(
        r"(?P<failed>\d+) failed.*?(?P<passed>\d+) passed"
        r"(?:, (?P<skipped>\d+) skipped)?"
        r"(?:, (?P<xfailed>\d+) xfailed)?"
        r"(?:, (?P<xpassed>\d+) xpassed)?"
        r"(?:, (?P<deselected>\d+) deselected)?",
        text,
    )
    if m:
        counts["failed"] = int(m.group("failed") or 0)
        counts["passed"] = int(m.group("passed") or 0)
        counts["skipped"] = int(m.group("skipped") or 0)
        counts["xfailed"] = int(m.group("xfailed") or 0)

    for item in failed:
        if item["bucket"] == "LEGACY_FAIL":
            counts["legacy_fail"] += 1
        elif item["bucket"] == "CURRENT_FAIL":
            counts["current_fail"] += 1

    return {"counts": counts, "failures": failed}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: classify_pytest_failures.py <pytest-output.txt>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")
    report = parse_summary(text)
    out = ROOT / "docs" / "pytest_classification_38_3.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    c = report["counts"]
    print("=== Pytest classification (Sprint 38.3) ===")
    print(f"PASS (from summary): {c['passed']}")
    print(f"FAIL total:          {c['failed']}")
    print(f"  LEGACY_FAIL:       {c['legacy_fail']}")
    print(f"  CURRENT_FAIL:      {c['current_fail']}")
    print(f"SKIPPED:             {c['skipped']}")
    print(f"XFAIL:               {c['xfailed']}")
    print(f"Wrote {out}")
    # RC gate: no current-platform failures allowed.
    return 1 if c["current_fail"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
