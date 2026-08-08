#!/usr/bin/env python3
"""Nightly platform validation — Sprint 39.0 Development Execution Policy.

Runs the daily full cycle and writes docs/NIGHTLY_REPORT.md.
Does not auto-fix failures; groups them for the next sprint backlog.

Usage:
  python scripts/nightly_validation.py
  python scripts/nightly_validation.py --skip-docker
  python scripts/nightly_validation.py --quick   # RC + protections + smoke only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "docs" / "NIGHTLY_REPORT.md"
REPORT_JSON = ROOT / "docs" / "nightly_report.json"
PYTEST_LOG = ROOT / "docs" / "nightly_pytest.txt"


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    duration_s: float = 0.0
    group: str = "general"


@dataclass
class NightlyReport:
    started_at: str
    finished_at: str = ""
    steps: list[StepResult] = field(default_factory=list)
    backlog: dict[str, list[str]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(s.ok for s in self.steps)


def _run(cmd: list[str], *, timeout: int, log_path: Path | None = None) -> tuple[bool, str]:
    print(f"+ {' '.join(cmd)}", flush=True)
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"timeout after {timeout}s: {exc}"
    out = (proc.stdout or "") + (proc.stderr or "")
    if log_path is not None:
        log_path.write_text(out, encoding="utf-8")
    # Keep detail short for markdown; full log may be in log_path
    tail = "\n".join(out.strip().splitlines()[-30:])
    return proc.returncode == 0, tail or f"exit={proc.returncode}"


def _classify_pytest(log_text: str) -> dict[str, list[str]]:
    classify = ROOT / "scripts" / "classify_pytest_failures.py"
    if not classify.exists() or not PYTEST_LOG.exists():
        return {}
    ok, _ = _run([sys.executable, str(classify), str(PYTEST_LOG)], timeout=120)
    path = ROOT / "docs" / "pytest_classification_38_3.json"
    # Prefer a nightly-specific copy if classifier wrote the shared path
    if not path.exists():
        return {"classifier": ["no classification artifact"]}
    data = json.loads(path.read_text(encoding="utf-8"))
    legacy = [f["line"] for f in data.get("failures", []) if f.get("bucket") == "LEGACY_FAIL"]
    current = [f["line"] for f in data.get("failures", []) if f.get("bucket") == "CURRENT_FAIL"]
    return {
        "legacy_fail": legacy[:80],
        "current_fail": current[:80],
        "summary": [
            f"passed={data.get('counts', {}).get('passed')}",
            f"failed={data.get('counts', {}).get('failed')}",
            f"legacy_fail={data.get('counts', {}).get('legacy_fail')}",
            f"current_fail={data.get('counts', {}).get('current_fail')}",
            f"classifier_ok={ok}",
        ],
    }


def run_nightly(*, skip_docker: bool, quick: bool) -> NightlyReport:
    started = datetime.now(timezone.utc)
    report = NightlyReport(started_at=started.isoformat())
    py = sys.executable

    def step(name: str, cmd: list[str], *, timeout: int, group: str) -> None:
        t0 = datetime.now(timezone.utc)
        log = PYTEST_LOG if name == "full_pytest" else None
        ok, detail = _run(cmd, timeout=timeout, log_path=log)
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        report.steps.append(StepResult(name=name, ok=ok, detail=detail, duration_s=dur, group=group))

    # Core always
    step(
        "ruff_critical",
        [
            py, "-m", "ruff", "check",
            "services", "repositories", "platform_security", "platform_jobs",
            "platform_sdk", "api",
            "--select", "E9,F63,F7,F82",
        ],
        timeout=180,
        group="static",
    )
    step("platform_protections", [py, "scripts/validate_platform_protections.py"], timeout=300, group="architecture")
    step("rc_tests", [py, "scripts/run_rc_test_suite.py"], timeout=600, group="rc")

    if not quick:
        step(
            "architecture_governance",
            [py, "scripts/validate_architecture.py"],
            timeout=900,
            group="architecture",
        )
        step(
            "legacy_migration",
            [py, "scripts/validate_legacy_migration.py"],
            timeout=300,
            group="architecture",
        )
        step(
            "security_suite",
            [
                py, "-m", "pytest",
                "tests/test_management_security.py",
                "tests/test_api_v1_freeze.py",
                "tests/test_admin_security.py",
                "-q", "--tb=no",
            ],
            timeout=600,
            group="security",
        )
        step(
            "full_pytest",
            [py, "-m", "pytest", "tests/", "-q", "--tb=line", "-m", "not slow"],
            timeout=2400,
            group="regression",
        )
        report.backlog = _classify_pytest(PYTEST_LOG.read_text(encoding="utf-8") if PYTEST_LOG.exists() else "")

    if not skip_docker:
        step(
            "docker_smoke",
            [py, "scripts/smoke_platform_rc.py", "--skip-down", "--no-rebuild"],
            timeout=900,
            group="docker",
        )
        # Optional clean rebuild path for true nightly
        if not quick:
            step(
                "docker_clean_up",
                ["docker", "compose", "up", "--build", "-d"],
                timeout=1200,
                group="docker",
            )
            step(
                "docker_smoke_after_build",
                [py, "scripts/smoke_platform_rc.py", "--skip-down", "--no-rebuild"],
                timeout=900,
                group="docker",
            )

    report.finished_at = datetime.now(timezone.utc).isoformat()
    return report


def write_report(report: NightlyReport) -> None:
    lines = [
        "# ADOS Nightly Validation Report",
        "",
        f"**Started (UTC):** {report.started_at}",
        f"**Finished (UTC):** {report.finished_at}",
        f"**Overall:** {'PASS' if report.passed else 'FAIL'}",
        "",
        "## Steps",
        "",
        "| Step | Group | Result | Duration (s) |",
        "|------|-------|--------|--------------|",
    ]
    for s in report.steps:
        mark = "PASS" if s.ok else "FAIL"
        lines.append(f"| `{s.name}` | {s.group} | **{mark}** | {s.duration_s:.1f} |")

    failed = [s for s in report.steps if not s.ok]
    lines += ["", "## Failures (grouped)", ""]
    if not failed and not report.backlog.get("current_fail"):
        lines.append("No gate failures.")
    else:
        by_group: dict[str, list[StepResult]] = {}
        for s in failed:
            by_group.setdefault(s.group, []).append(s)
        for group, items in sorted(by_group.items()):
            lines.append(f"### {group}")
            for s in items:
                lines.append(f"- **{s.name}**")
                if s.detail:
                    lines.append("")
                    lines.append("```")
                    lines.append(s.detail[:4000])
                    lines.append("```")
                lines.append("")

    if report.backlog:
        lines += ["", "## Pytest classification backlog (do not auto-fix)", ""]
        for key, items in report.backlog.items():
            lines.append(f"### {key}")
            if not items:
                lines.append("_empty_")
            else:
                for item in items[:50]:
                    lines.append(f"- `{item}`")
            lines.append("")
        lines += [
            "## Next sprint actions",
            "",
            "1. Triage `current_fail` first (if any).",
            "2. Keep `legacy_fail` as version-pin debt unless an INFRASTRUCTURE sprint retires them.",
            "3. Do not bulk-auto-fix overnight failures without a scoped sprint.",
            "",
        ]

    lines += [
        "---",
        f"_Generated by `scripts/nightly_validation.py` per `docs/DEVELOPMENT_EXECUTION_POLICY.md`._",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    REPORT_JSON.write_text(
        json.dumps(
            {
                "started_at": report.started_at,
                "finished_at": report.finished_at,
                "passed": report.passed,
                "steps": [asdict(s) for s in report.steps],
                "backlog_keys": list(report.backlog.keys()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-docker", action="store_true")
    parser.add_argument("--quick", action="store_true", help="Skip full pytest / clean rebuild")
    args = parser.parse_args()
    # Ensure ruff present
    try:
        import ruff  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ruff==0.9.10"], cwd=ROOT, check=False)

    report = run_nightly(skip_docker=args.skip_docker, quick=args.quick)
    write_report(report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
