#!/usr/bin/env python3
"""Minimal Vanguard + Recruiting API for Playwright E2E (same handlers as production)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("REDIS_REQUIRED", "false")
os.environ.setdefault("VANGUARD_ANTIBOT_PROVIDER", "none")
os.environ.setdefault("VANGUARD_APPLY_RATE_LIMIT", "50")

from aiohttp import web

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes


def main() -> None:
    app = web.Application()
    register_recruiting_enterprise_routes(app)
    register_vanguard_site_routes(app)
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8080"))
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
