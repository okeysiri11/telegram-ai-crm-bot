#!/usr/bin/env python3
"""Sprint 41.1 — GlobeFly first-client journey probe (SPA + API health)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"
WEB = "http://127.0.0.1"
OUT = ROOT / "docs" / "acceptance_41_1_probe.json"

JOURNEY_PATHS = [
    ("login", "/login"),
    ("dashboard", "/dashboard"),
    ("crm", "/crm"),
    ("leads", "/crm?view=leads"),
    ("clients", "/crm?view=clients"),
    ("deals", "/crm?view=deals"),
    ("documents", "/documents"),
    ("ai", "/ai-agents"),
    ("reports", "/analytics"),
    ("tasks", "/tasks"),
    ("calendar", "/calendar"),
    ("settings", "/settings"),
    ("profile", "/identity/profile"),
    ("logout", "/auth/logout"),
]

HIDDEN_FOR_CLIENT = [
    "/platform-builder/builder-studio",
    "/command-runtime",
    "/ai-studio",
    "/kernel",
    "/owner",
]


def get(url: str) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read(200).decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def main() -> int:
    health, _ = get(f"{API}/health")
    ready, _ = get(f"{API}/ready")
    steps = []
    for name, path in JOURNEY_PATHS:
        code, _ = get(f"{WEB}{path}")
        steps.append({"step": name, "path": path, "http": code, "ok": code == 200})
    hidden = []
    for path in HIDDEN_FOR_CLIENT:
        code, _ = get(f"{WEB}{path}")
        # SPA still serves 200; UI guard hides — record availability only
        hidden.append({"path": path, "spa_http": code})

    pipeline_code, _ = get(f"{API}/api/auto/v1/crm/pipeline")
    report = {
        "sprint": "41.1",
        "client": "GlobeFly",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "health": health,
        "ready": ready,
        "journey": steps,
        "client_hidden_routes_spa": hidden,
        "crm_pipeline_unauth": pipeline_code,
        "demo_login": "client@globefly.demo / demo (tenant globefly)",
        "view_modes": ["client", "manager", "company_admin", "platform_owner", "developer"],
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"health": health, "ready": ready, "out": str(OUT)}, indent=2))
    ok = health == 200 and ready == 200 and all(s["ok"] for s in steps)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
