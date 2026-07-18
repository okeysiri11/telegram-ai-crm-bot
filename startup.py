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
    from auto_vertical_handlers import auto_vertical_router as auto_router
    from handlers import router
    from routers.auto_client_router import router as auto_client_entry_router
    from routers.auto_dealer_router import router as auto_dealer_entry_router
    from routers.auto_hub_router import router as auto_hub_router
    from routers.client_history_router import router as client_history_router
    from routers.manager_crm_router import router as manager_crm_router
    from routers.manager_dashboard_router import router as manager_dashboard_router
    from routers.manager_debug_router import router as manager_debug_router
    from routers.realty_router import router as realty_router

    dp.include_router(auto_client_entry_router)
    dp.include_router(auto_dealer_entry_router)
    dp.include_router(client_history_router)
    dp.include_router(manager_crm_router)
    dp.include_router(manager_dashboard_router)
    dp.include_router(manager_debug_router)
    dp.include_router(auto_hub_router)
    dp.include_router(realty_router)
    dp.include_router(auto_router)
    dp.include_router(router)
    logger.info("Registered routers: %s", ", ".join(BOT_ROUTER_PATHS))


@dataclass
class StartupContext:
    scheduler: Any
    runner: web.AppRunner | None
    startup: dict[str, Any]
    diagnostics: dict[str, Any]
    escalation_task: Any = None


async def run_startup() -> StartupContext:
    from platform_identity.jwt_service import validate_iam_jwt_secret

    validate_iam_jwt_secret()

    from api.server import start_api_server
    from services.bidex_telegram_quote_parser import configure_bidex_parser
    from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1
    from services.pg_scheduler_engine import get_default_worker
    from services.pg_webhook_engine import WebhookEngineV1

    configure_bidex_parser(DealerQuoteAuthorityEngineV1)
    logger.info("Dealer quote engine initialized")
    logger.info("BidEx parser initialized")

    WebhookEngineV1.register_event_handlers()
    from events.handlers import register_platform_event_handlers

    register_platform_event_handlers()
    logger.info("Platform internal event handlers registered")

    from services import crm_event_bus as event_bus

    await event_bus.get_default_worker().start()
    logger.info("CRM event bus workers started for platform metrics and webhooks")

    scheduler = get_default_worker()
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
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        seed = await PlatformPermissionsEngineV1.ensure_seeded()
        logger.info("Platform permissions seed: %s", seed)
    except Exception:
        logger.warning("Platform permissions seed failed", exc_info=True)

    try:
        from services.pg_vertical_routing_engine import VerticalRoutingEngineV1

        routing_seed = await VerticalRoutingEngineV1.ensure_platform_actors()
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

    from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

    diagnostics = await ManagerDeliveryEngineV1.startup_diagnostics()
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
        from services import crm_event_bus as event_bus

        await event_bus.get_default_worker().shutdown()
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
