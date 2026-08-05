#!/usr/bin/env python3
"""Staging / pilot smoke — Sprint 30.6 Platform Integration.

Validates critical web routes, launch catalog tokens, sprint pins,
and presence of governance/audit/integration foundations — without starting a browser.

Usage:
  PYTHONPATH=. python3 scripts/ga_staging_smoke.py
  PYTHONPATH=. python3 scripts/ga_staging_smoke.py --base-url http://127.0.0.1:5180
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_APP_TOKENS = [
    'path="/enterprise-city"',
    'path="/city"',
    'path="/ai-agents"',
    'path="/health"',
    'path="/production-studio"',
    'path="/demo/scenario"',
    'path="/platform-builder/concierge"',
    'path="/platform-builder/control-tower"',
    'path="/platform-builder/mission-control"',
    "RouteErrorBoundary",
    "PlatformHealthPage",
    "PlatformErrorPage",
]

REQUIRED_FILES = [
    "docs/API_EDGE_GOVERNANCE_PLAN.md",
    "docs/IMMUTABLE_AUDIT_VAULT_FOUNDATION.md",
    "docs/PILOT_CHECKLIST.md",
    "docs/DEPLOYMENT_CHECKLIST_1_1_1.md",
    "docs/PLATFORM_BOOT.md",
    "docs/LIVE_DEMO.md",
    "docs/INTEGRATION_REPORT.md",
    "docs/BETA_CHECKLIST.md",
    "docs/SPRINT_30_6_RESULT.md",
    "src/web/src/enterprise-governance/governanceEdge.ts",
    "src/web/src/audit-vault/foundation.ts",
    "src/web/src/shell/RouteErrorBoundary.tsx",
    "src/web/src/enterprise-control-tower/ControlTowerStrip.tsx",
    "src/web/src/platform-integration/platformBoot.ts",
    "src/web/src/platform-integration/PlatformHealthPage.tsx",
]


def check_files() -> list[str]:
    errs: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errs.append(f"missing file: {rel}")
    return errs


def check_app_routes() -> list[str]:
    errs: list[str] = []
    app = (ROOT / "src/web/src/App.tsx").read_text()
    for token in CRITICAL_APP_TOKENS:
        if token not in app:
            errs.append(f"App.tsx missing token: {token}")
    return errs


def check_versions() -> list[str]:
    errs: list[str] = []
    cfg = (ROOT / "applications/platform_builder/config.py").read_text()
    if 'application_version: str = "1.67.0"' not in cfg:
        errs.append("config application_version != 1.67.0")
    if "General Availability" not in cfg:
        errs.append("config missing General Availability")
    web = (ROOT / "src/web/src/config/webConfig.ts").read_text()
    if 'sprint: "30.6"' not in web:
        errs.append("webConfig sprint != 30.6")
    boot = (ROOT / "src/web/src/platform-integration/platformBoot.ts").read_text()
    if 'PLATFORM_BOOT_VERSION = "30.6"' not in boot:
        errs.append("PLATFORM_BOOT_VERSION != 30.6")
    return errs


def check_http(base: str) -> list[str]:
    errs: list[str] = []
    url = base.rstrip("/") + "/"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status >= 400:
                errs.append(f"HTTP {resp.status} for {url}")
    except urllib.error.URLError as exc:
        errs.append(f"HTTP unreachable {url}: {exc.reason}")
    except Exception as exc:  # noqa: BLE001
        errs.append(f"HTTP error {url}: {exc}")
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="GA staging / pilot smoke")
    parser.add_argument("--base-url", default="", help="Optional running web origin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors = check_files() + check_app_routes() + check_versions()
    if args.base_url:
        errors.extend(check_http(args.base_url))

    report = {
        "ok": not errors,
        "sprint": "30.6",
        "product": "Enterprise Platform · Integration & Live Demo",
        "errors": errors,
        "checks": {
            "files": len(REQUIRED_FILES),
            "route_tokens": len(CRITICAL_APP_TOKENS),
            "http": bool(args.base_url),
        },
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("GA Staging Smoke — Sprint 30.6")
        print("OK" if report["ok"] else "FAIL")
        for e in errors:
            print(f"  - {e}")
        if report["ok"]:
            print("All static pilot validation checks passed.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
