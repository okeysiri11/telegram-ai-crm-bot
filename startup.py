# Application startup — background services, API, diagnostics before polling.

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from config import API_HOST, API_PORT, DEFAULT_AUTO_MANAGER_ID
from middleware.entry_point_middleware import EntryPointMiddleware
from middleware.tenant_middleware import TenantMiddleware

logger = logging.getLogger(__name__)

# Registered bot routers (order matters — first match wins).
BOT_ROUTER_PATHS: tuple[str, ...] = (
    "routers.auto_client_router",
    "routers.auto_dealer_router",
    "routers.client_history_router",
    "routers.manager_crm_router",
    "routers.manager_dashboard_router",
    "routers.manager_debug_router",
    "routers.auto_hub_router",
    "routers.realty_router",
    "auto_vertical_handlers",
    "handlers",
)


def register_routers(dp: Dispatcher) -> None:
    from platform_legacy import legacy

    legacy.telegram.register_bot_routers(dp)
    logger.info("Registered routers: %s", ", ".join(BOT_ROUTER_PATHS))


@dataclass
class StartupContext:
    scheduler: Any
    runner: web.AppRunner | None
    startup: dict[str, Any]
    diagnostics: dict[str, Any]
    escalation_task: Any = None


async def run_startup() -> StartupContext:
    from platform_configuration.configuration_center import configuration_center

    configuration_center.load()
    configuration_center.validate(fail_fast=False)
    logger.info("ConfigurationCenter loaded: %s", configuration_center.diagnostics()["validation"])

    from platform_identity.jwt_service import validate_iam_jwt_secret

    validate_iam_jwt_secret()

    from api.server import start_api_server
    from platform_legacy import legacy

    legacy.bootstrap.configure_bidex_parser()
    logger.info("Dealer quote engine initialized")
    logger.info("BidEx parser initialized")

    legacy.bootstrap.register_webhook_handlers()
    from events.handlers import register_platform_event_handlers

    register_platform_event_handlers()
    logger.info("Platform internal event handlers registered")

    from events.crm_publisher import get_crm_worker

    await get_crm_worker().start()
    logger.info("CRM event bus workers started for platform metrics and webhooks")

    scheduler = legacy.scheduler.get_default_worker()
    await scheduler.start()
    runner = await start_api_server(host=API_HOST, port=API_PORT)
    if runner is not None:
        logger.info(
            "API server listening on http://%s:%s/health (liveness/readiness enabled)",
            API_HOST,
            API_PORT,
        )
    else:
        logger.warning(
            "API server skipped — port %s busy or unavailable. Set API_PORT in .env to change.",
            API_PORT,
        )

    from services.production_readiness_suite import ProductionReadinessSuite

    startup = await ProductionReadinessSuite.validate_startup()
    logger.info(
        "Production readiness startup: status=%s ready=%s",
        startup.get("status"),
        startup.get("ready"),
    )

    try:
        from services.observability import configure_structured_logging, init_sentry
        from config import LOG_LEVEL

        configure_structured_logging(LOG_LEVEL)
        init_sentry()
    except Exception:
        logger.warning("Observability init failed", exc_info=True)

    from config import POSTGRES_ONLY, REDIS_REQUIRED, REDIS_URL

    logger.info(
        "Storage policy: POSTGRES_ONLY=%s REDIS_REQUIRED=%s REDIS_URL=%s",
        POSTGRES_ONLY,
        REDIS_REQUIRED,
        "set" if REDIS_URL else "missing",
    )

    try:
        seed = await legacy.permissions.ensure_permissions_seeded()
        logger.info("Platform permissions seed: %s", seed)
    except Exception:
        logger.warning("Platform permissions seed failed", exc_info=True)

    try:
        routing_seed = await legacy.bootstrap.ensure_vertical_routing()
        logger.info("Vertical routing seed: %s", routing_seed)
    except Exception:
        logger.warning("Vertical routing seed failed", exc_info=True)

    try:
        from services.manager_pool_service import manager_pool_service

        pool_seed = await manager_pool_service.bootstrap_from_config()
        logger.info("Manager pool bootstrap: %s", pool_seed)
    except Exception:
        logger.warning("Manager pool bootstrap failed", exc_info=True)

    try:
        from platform_configuration.config_service import configuration_service

        config_boot = await configuration_service.bootstrap(include_env=True)
        logger.info("Platform configuration bootstrap: %s", config_boot)
    except Exception:
        logger.warning("Platform configuration bootstrap failed", exc_info=True)

    try:
        from platform_sdk.bootstrap import bootstrap_platform_sdk

        sdk_boot = await bootstrap_platform_sdk()
        logger.info("Platform SDK bootstrap: %s", sdk_boot)
    except Exception:
        logger.warning("Platform SDK bootstrap failed", exc_info=True)

    diagnostics = await legacy.notifications.startup_diagnostics()
    logger.info("Manager startup diagnostics: %s", diagnostics)

    manager_id = diagnostics.get("internal_user_id")
    if manager_id:
        logger.info(
            "Auto manager ready: telegram_id=%s uuid=%s roles=%s",
            DEFAULT_AUTO_MANAGER_ID,
            manager_id,
            diagnostics.get("roles"),
        )
    else:
        logger.warning("AUTO_MANAGER is not provisioned")
    if not startup.get("ready"):
        logger.warning(
            "Startup validation issues: unhealthy=%s degraded=%s",
            startup.get("unhealthy"),
            startup.get("degraded"),
        )

    # Background escalation worker (every 30s, EventBus-only side effects)
    from workers.escalation_worker import get_escalation_worker

    escalation_worker = get_escalation_worker()
    await escalation_worker.start()

    return StartupContext(
        scheduler=scheduler,
        runner=runner,
        startup=startup,
        diagnostics=diagnostics,
        escalation_task=escalation_worker,
    )


async def shutdown_startup(context: StartupContext) -> None:
    from database.session import shutdown_db

    try:
        from events.crm_publisher import get_crm_worker

        await get_crm_worker().shutdown()
    except Exception:
        logger.warning("Event bus shutdown failed", exc_info=True)

    task = getattr(context, "escalation_task", None)
    if task is not None and hasattr(task, "stop"):
        await task.stop()
    elif task is not None:
        task.cancel()
    await context.scheduler.shutdown()
    if context.runner is not None:
        await context.runner.cleanup()
    await shutdown_db()
