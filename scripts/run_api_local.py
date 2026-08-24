#!/usr/bin/env python3
"""Start ADOS HTTP API only (no Telegram bot) — Sprint 32.6B zero-touch local.

Usage:
  ./venv/bin/python scripts/run_api_local.py
  ENVIRONMENT=development REDIS_REQUIRED=false ./venv/bin/python scripts/run_api_local.py

Automatically:
  - forces local Redis-optional mode
  - runs Alembic migrations (unless ADOS_SKIP_MIGRATIONS=1)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Local-friendly defaults before ConfigurationCenter loads.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("REDIS_REQUIRED", "false")
os.environ.setdefault("POSTGRES_ONLY", "true")
os.environ.setdefault("API_HOST", "127.0.0.1")
os.environ.setdefault("API_PORT", "8080")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_api_local")


def _force_local_env() -> None:
    """Re-apply local overrides after dotenv (demo-friendly, zero-touch)."""
    os.environ.setdefault("ENVIRONMENT", "development")
    # Explicit false must win over POSTGRES_ONLY→require Redis (Sprint 32.6B).
    if os.getenv("ADOS_REQUIRE_REDIS", "").lower() not in {"1", "true", "yes"}:
        os.environ["REDIS_REQUIRED"] = "false"
    # If Redis is down but URL is set, readiness soft-fails; keep URL for when Redis returns.


def _run_migrations() -> None:
    from scripts.ensure_local_schema import ensure_schema

    code = ensure_schema()
    if code != 0:
        # Non-fatal when DB unreachable — API may still serve demo auth / liveness.
        logger.warning(
            "schema migration exited %s — continuing (set ADOS_FAIL_ON_MIGRATE=1 to abort)",
            code,
        )
        if os.getenv("ADOS_FAIL_ON_MIGRATE", "").lower() in {"1", "true", "yes"}:
            raise SystemExit(code)


async def _main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        pass

    _force_local_env()
    _run_migrations()

    from platform_configuration.configuration_center import configuration_center
    from platform_configuration.env_source import load_environment

    load_environment.cache_clear()
    configuration_center._settings = None  # noqa: SLF001
    configuration_center.load()
    configuration_center.validate(fail_fast=False)
    logger.info("config validation: %s", configuration_center.diagnostics().get("validation"))
    logger.info(
        "local mode: redis.required=%s postgres_only=%s",
        configuration_center.settings.redis.required,
        configuration_center.settings.database.postgres_only,
    )

    # Prefer JWT_SECRET when IAM unset (dev).
    try:
        from platform_identity.jwt_service import validate_iam_jwt_secret

        validate_iam_jwt_secret()
    except RuntimeError as exc:
        logger.warning("IAM JWT soft-fail in local API mode: %s", exc)
        logger.warning("Set IAM_JWT_SECRET or JWT_SECRET in .env for signed management tokens")

    from api.bind import resolve_api_host, resolve_api_port
    from api.server import start_api_server
    from config import API_HOST, API_PORT

    host = resolve_api_host(API_HOST or "127.0.0.1")
    port = resolve_api_port(API_PORT or 8080)

    # Optional light workers — skip if Redis/deps unavailable.
    try:
        from events.handlers import register_platform_event_handlers

        register_platform_event_handlers()
        logger.info("platform event handlers registered")
    except Exception:
        logger.exception("event handlers skipped")

    # Optional CRM worker — off by default for local demo (needs Redis + full schema).
    if os.getenv("ADOS_LOCAL_CRM_WORKER", "").lower() in {"1", "true", "yes"}:
        try:
            from events.crm_publisher import get_crm_worker

            await get_crm_worker().start()
            logger.info("CRM event bus worker started")
        except Exception:
            logger.warning("CRM worker not started", exc_info=True)
    else:
        logger.info("CRM worker skipped (set ADOS_LOCAL_CRM_WORKER=1 to enable)")

    runner = await start_api_server(host=host, port=port)
    if runner is None:
        logger.error("API failed to bind %s:%s", host, port)
        return 1

    logger.info("ADOS API listening on http://%s:%s/health", host, port)
    logger.info("Press Ctrl+C to stop")
    stop = asyncio.Event()
    try:
        await stop.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_main()))
    except KeyboardInterrupt:
        logger.info("API stopped")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
