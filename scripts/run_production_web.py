#!/usr/bin/env python3
"""Durable production web entrypoint — API + same-origin SPA (Sprint 13.1).

This is the process a durable host (Render/Railway/Fly/VPS Docker) runs:

  1. loads ConfigurationCenter and validates it — **fail-fast in production**
     (no silent fallback to demo/dev behavior);
  2. validates the IAM JWT secret (raises on insecure production secrets);
  3. applies Alembic migrations — **fatal in production** on failure
     (set ADOS_SKIP_MIGRATIONS=1 only when migrations run out-of-band);
  4. serves the production SPA build same-origin (ADOS_SERVE_WEB, on by
     default here) — fails loudly if the build is missing while enabled;
  5. starts platform event handlers, the CRM event-bus worker, and the
     scheduler worker, then binds the API server to 0.0.0.0:$PORT
     (provider-injected PORT honored via api.bind);
  6. shuts down gracefully on SIGTERM/SIGINT (provider redeploys).

Telegram polling is NOT started — the bot remains a separate run target
(main.py). Set ADOS_TELEGRAM_REQUIRED=false in the deployment manifest when
this service intentionally runs without BOT_TOKEN (see
services/production_readiness_suite.py).
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Web service profile defaults — explicit env always wins.
os.environ.setdefault("ADOS_SERVE_WEB", "true")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_production_web")


def _fatal(message: str) -> None:
    logger.error("FATAL: %s", message)
    raise SystemExit(1)


def _run_migrations(*, is_production: bool) -> None:
    from scripts.ensure_local_schema import ensure_schema

    code = ensure_schema()
    if code != 0:
        if is_production:
            _fatal(f"alembic upgrade head failed (exit {code}) — refusing to start production")
        logger.warning("schema migration exited %s — continuing (non-production)", code)


def _check_frontend() -> None:
    from api.web_static import serve_web_enabled, web_dist_dir

    flag = (os.environ.get("ADOS_SERVE_WEB") or "").strip().lower()
    if flag in {"1", "true", "yes", "on"} and not serve_web_enabled():
        _fatal(
            f"ADOS_SERVE_WEB is enabled but the production build is missing: "
            f"{web_dist_dir()}/index.html (build src/web first)"
        )


async def _main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        pass

    from platform_configuration.configuration_center import configuration_center

    configuration_center.load()
    is_production = configuration_center.settings.is_production
    # TD-57 semantics preserved: fail closed in production, warn in development.
    configuration_center.validate(fail_fast=is_production)
    logger.info(
        "config validation: %s (runtime=%s)",
        configuration_center.diagnostics().get("validation"),
        "production" if is_production else "development",
    )

    from platform_identity.jwt_service import validate_iam_jwt_secret

    validate_iam_jwt_secret()

    _run_migrations(is_production=is_production)
    _check_frontend()

    from events.handlers import register_platform_event_handlers

    register_platform_event_handlers()
    logger.info("platform event handlers registered")

    from events.crm_publisher import get_crm_worker

    await get_crm_worker().start()
    logger.info("CRM event bus worker started")

    from services.pg_scheduler_engine import get_default_worker

    scheduler = get_default_worker()
    await scheduler.start()
    logger.info("scheduler worker started")

    from api.bind import resolve_api_host, resolve_api_port
    from api.server import start_api_server

    host = resolve_api_host("0.0.0.0")
    port = resolve_api_port()
    runner = await start_api_server(host=host, port=port)
    if runner is None:
        _fatal(f"API server failed to bind {host}:{port}")

    from services.production_readiness_suite import ProductionReadinessSuite

    startup = await ProductionReadinessSuite.validate_startup()
    logger.info(
        "production readiness: status=%s ready=%s unhealthy=%s degraded=%s",
        startup.get("status"),
        startup.get("ready"),
        startup.get("unhealthy"),
        startup.get("degraded"),
    )
    if is_production and not startup.get("ready"):
        # Loud but non-fatal: /readiness reports 503 and the platform health
        # check keeps traffic off this instance until dependencies recover.
        logger.error("production readiness NOT ready — /readiness will return 503")

    logger.info("ADOS production web listening on http://%s:%s (liveness/readiness enabled)", host, port)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        await stop.wait()
    finally:
        logger.info("shutting down (graceful)")
        try:
            await get_crm_worker().shutdown()
        except Exception:
            logger.warning("CRM worker shutdown failed", exc_info=True)
        try:
            await scheduler.shutdown()
        except Exception:
            logger.warning("scheduler shutdown failed", exc_info=True)
        await runner.cleanup()
        from database.session import shutdown_db

        await shutdown_db()
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
