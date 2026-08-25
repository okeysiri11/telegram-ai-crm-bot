#!/usr/bin/env python3
"""Sprint 13.1 — CRM + health smoke. Never mutates CRM. Never prints secrets."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

SECRET_MARKERS = ("password", "secret", "token=", "postgresql+", "postgresql://", "redis://")


def _get(url: str, *, headers: dict[str, str] | None = None, timeout: int = 8) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"text": raw[:200]}
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"text": raw[:200]}
        return exc.code, payload


def _no_secrets(payload: Any) -> bool:
    blob = json.dumps(payload).lower()
    return not any(marker in blob for marker in SECRET_MARKERS)


def smoke_payloads(*, liveness: dict, unauth_manager: int) -> dict[str, bool]:
    return {
        "liveness_alive": liveness.get("status") == "alive",
        "liveness_identity": bool(liveness.get("service") and liveness.get("revision")),
        "liveness_no_secrets": _no_secrets(liveness),
        "manager_unauth_denied": unauth_manager == 401,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="", help="Optional live base URL. Offline if omitted.")
    args = parser.parse_args()
    if not args.base_url:
        print("CRM_SMOKE=OFFLINE (no --base-url; contract tests cover the same paths)")
        return 0
    base = args.base_url.rstrip("/")
    live_status, live_body = _get(f"{base}/liveness")
    mgr_status, _ = _get(f"{base}/api/auto/v1/crm/manager/command-center")
    summary_status, _ = _get(f"{base}/api/auto/v1/crm/manager/operational-summary")
    checks = smoke_payloads(liveness=live_body if isinstance(live_body, dict) else {}, unauth_manager=mgr_status)
    checks["liveness_http"] = live_status == 200
    checks["operational_summary_unauth"] = summary_status == 401
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "failed": failed}, indent=2))
    print("CRM_SMOKE=" + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
