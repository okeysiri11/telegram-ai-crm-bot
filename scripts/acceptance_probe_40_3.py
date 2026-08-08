#!/usr/bin/env python3
"""Sprint 40.3 — Web UI acceptance probe (SPA HTTP + OpenAPI + auth pages).

Records nginx SPA availability for operator-facing routes. In-app redirects
are covered by vitest; nginx always returns 200 + index.html for SPA paths.
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
OUT = ROOT / "docs" / "acceptance_40_3_probe.json"

WEB_PATHS = [
    "/login",
    "/auth/logout",
    "/auth/unauthorized",
    "/dashboard",
    "/crm",
    "/crm?view=leads",
    "/crm?view=clients",
    "/crm?view=deals",
    "/crm?view=companies",
    "/deals",
    "/clients",
    "/companies",
    "/leads",
    "/reports",
    "/tasks",
    "/calendar",
    "/documents",
    "/knowledge",
    "/ai-agents",
    "/ai-studio",
    "/analytics",
    "/notifications",
    "/settings",
    "/profile",
    "/identity/profile",
    "/admin",
    "/marketplace",
    "/desktop",
    "/api/v1/docs",  # via nginx proxy? may 404 on web host — also probe API
]

API_PATHS = [
    "/health",
    "/ready",
    "/api/v1/openapi.json",
    "/api/v1/docs",
    "/api/v1/leads",
    "/api/v1/clients",
    "/api/v1/reports",
]


def fetch(url: str) -> dict:
    req = Request(url, headers={"Accept": "*/*"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read(400)
            return {
                "url": url,
                "status": r.status,
                "ok": 200 <= r.status < 400,
                "body_prefix": raw[:160].decode("utf-8", "replace"),
            }
    except urllib.error.HTTPError as e:
        raw = e.read(400)
        return {
            "url": url,
            "status": e.code,
            "ok": False,
            "body_prefix": raw[:160].decode("utf-8", "replace"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "status": None, "ok": False, "body_prefix": str(exc)}


def main() -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sprint": "40.3",
        "web": [fetch(WEB + p) for p in WEB_PATHS],
        "api": [fetch(API + p) for p in API_PATHS],
        "notes": [
            "SPA paths return HTTP 200 from nginx even when React redirects; use vitest for in-app alias checks.",
            "GET /api/v1/leads without auth expects 401 (registered, not 501).",
        ],
    }
    # Classify API leads
    leads = next((r for r in report["api"] if r["url"].endswith("/api/v1/leads")), None)
    report["checks"] = {
        "leads_not_501": bool(leads and leads.get("status") != 501),
        "openapi_ok": any(r["url"].endswith("openapi.json") and r.get("status") == 200 for r in report["api"]),
        "docs_ok": any(r["url"].endswith("/docs") and r.get("status") == 200 for r in report["api"]),
        "health_ok": any(r["url"].endswith("/health") and r.get("status") == 200 for r in report["api"]),
        "ready_ok": any(r["url"].endswith("/ready") and r.get("status") == 200 for r in report["api"]),
        "web_all_reachable": all(r.get("status") == 200 for r in report["web"] if "/api/v1" not in r["url"]),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["checks"], indent=2))
    print(f"Wrote {OUT}")
    failed = [k for k, v in report["checks"].items() if not v]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
