#!/usr/bin/env python3
"""Sprint 40.0 acceptance probe — records findings; does not fix code.

Writes docs/acceptance_40_0_probe.json used by GLOBEFLY_READINESS / RESULT docs.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"
WEB = "http://127.0.0.1"


def fetch(url: str, method: str = "GET", data: dict | None = None):
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read(2000)
            return {"url": url, "method": method, "status": r.status, "ok": 200 <= r.status < 300, "body_prefix": raw[:240].decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        raw = e.read(2000)
        return {"url": url, "method": method, "status": e.code, "ok": False, "body_prefix": raw[:240].decode("utf-8", "replace")}
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "method": method, "status": None, "ok": False, "body_prefix": str(exc)}


def main() -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "startup": {},
        "web_routes": [],
        "api": [],
        "bugs": [],
    }

    for path in ("/health", "/ready"):
        report["startup"][path] = fetch(API + path)

    web_paths = [
        "/login", "/auth/logout", "/dashboard", "/crm", "/crm?view=deals",
        "/crm?view=clients", "/crm?view=companies", "/tasks", "/calendar",
        "/ai-agents", "/knowledge", "/documents", "/analytics", "/notifications",
        "/settings", "/deals", "/clients", "/companies", "/reports",
    ]
    for path in web_paths:
        report["web_routes"].append(fetch(WEB + path))

    api_cases = [
        ("GET", "/api/auto/v1/crm/customers"),
        ("GET", "/api/auto/v1/crm/leads"),
        ("GET", "/api/auto/v1/crm/deals"),
        ("GET", "/api/auto/v1/crm/pipeline"),
        ("GET", "/api/auto/v1/crm/tasks"),
        ("POST", "/api/auto/v1/crm/leads", {"name": "GF Lead", "source": "web", "utm_source": "globefly", "utm_medium": "site", "utm_campaign": "launch"}),
        ("POST", "/api/auto/v1/crm/leads", {"name": "Bad Source", "source": "not-a-real-source"}),
        ("POST", "/api/auto/v1/crm/deals", {"title": "GF Deal", "stage": "prospect"}),
        ("POST", "/api/auto/v1/crm/customers", {"name": "GF Contact"}),
        ("POST", "/api/auto/v1/crm/tasks", {"title": "Follow up", "status": "open"}),
        ("GET", "/api/v1/leads"),
        ("GET", "/api/v1/deals"),
        ("GET", "/management/v1/system"),
        ("GET", "/api/v1/does-not-exist-zzzz"),
        ("GET", "/api/auto/v1/crm/leads/missing-id-zzzz"),
    ]
    for case in api_cases:
        method, path = case[0], case[1]
        data = case[2] if len(case) > 2 else None
        report["api"].append(fetch(API + path, method=method, data=data))

    # Derived bugs (acceptance only)
    for row in report["api"]:
        if row["method"] == "POST" and "not-a-real-source" in row.get("body_prefix", "") or (
            row["method"] == "POST" and row["url"].endswith("/crm/leads") and row["status"] == 500
        ):
            if row["status"] == 500:
                report["bugs"].append({
                    "id": "ACC-40-001",
                    "severity": "Critical",
                    "area": "API/CRM leads",
                    "summary": "Invalid LeadSource returns HTTP 500 instead of 400",
                    "evidence": row,
                })
        if row["url"].endswith("/api/v1/leads") and row["status"] == 501:
            report["bugs"].append({
                "id": "ACC-40-002",
                "severity": "Major",
                "area": "API/v1",
                "summary": "GET /api/v1/leads is reserved 501; real leads live under /api/auto/v1/crm/leads",
                "evidence": row,
            })
        if "/api/auto/v1/crm/" in row["url"] and row["method"] == "GET" and row["status"] == 200:
            # note once
            pass

    # Unauthenticated CRM write surface
    open_writes = [r for r in report["api"] if r["method"] == "POST" and "/api/auto/v1/crm/" in r["url"] and r["status"] in (200, 201)]
    if open_writes:
        report["bugs"].append({
            "id": "ACC-40-003",
            "severity": "Critical",
            "area": "Security/CRM",
            "summary": "Auto CRM write endpoints accept unauthenticated POST (201) — not acceptable for commercial GlobeFly traffic without gateway auth",
            "evidence": open_writes[:3],
        })

    report["bugs"].extend([
        {
            "id": "ACC-40-004",
            "severity": "Major",
            "area": "WEB routing",
            "summary": "Top-level /deals /clients /companies /reports are not App routes; SPA falls through to PlatformErrorPage 404 (nginx still returns 200 HTML shell)",
            "evidence": {"routes": ["/deals", "/clients", "/companies", "/reports"], "canonical": "/crm?view=*"},
        },
        {
            "id": "ACC-40-005",
            "severity": "Major",
            "area": "WEB navigation",
            "summary": "Enterprise shell nav still links some modules to /workspace/* while Ru/catalog use /crm /documents /analytics — path drift for operators",
            "evidence": {"shell": "/workspace/crm", "catalog": "/crm"},
        },
        {
            "id": "ACC-40-006",
            "severity": "Major",
            "area": "WEB analytics/reports",
            "summary": "/analytics mounts generic EnterpriseModulePage; dedicated /reports route missing (workspace shell only)",
            "evidence": {"analytics": "/analytics", "reports": "/workspace/reports/weekly"},
        },
        {
            "id": "ACC-40-007",
            "severity": "Major",
            "area": "Marketing tags",
            "summary": "No Google Tag Manager, GA4, or Meta Pixel integration found in frontend or docs",
            "evidence": {"search": "none"},
        },
        {
            "id": "ACC-40-008",
            "severity": "Minor",
            "area": "Email",
            "summary": "SMTP connector exists but outbound email is not validated as configured for GlobeFly (SMTP_HOST may be empty)",
            "evidence": {"connector": "applications/enterprise_hub/integrations/connectors/smtp.py"},
        },
        {
            "id": "ACC-40-009",
            "severity": "Cosmetic",
            "area": "WEB shell",
            "summary": "Enterprise City nav item marked comingSoon in enterpriseNav while other catalogs mark City GA",
            "evidence": {"file": "src/web/src/shell/enterprise/enterpriseNav.ts"},
        },
    ])

    # Deduplicate ACC-40-001 if duplicated
    seen = set()
    uniq = []
    for b in report["bugs"]:
        if b["id"] in seen:
            continue
        seen.add(b["id"])
        uniq.append(b)
    report["bugs"] = uniq

    out = ROOT / "docs" / "acceptance_40_0_probe.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"bugs={len(report['bugs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
