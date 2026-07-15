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
    "routers.manager_debug_router",
    "routers.auto_hub_router",
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
    from routers.manager_debug_router import router as manager_debug_router

    dp.include_router(auto_client_entry_router)
    dp.include_router(auto_dealer_entry_router)
    dp.include_router(client_history_router)
    dp.include_router(manager_crm_router)
    dp.include_router(manager_debug_router)
    dp.include_router(auto_hub_router)
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
    from api.server import start_api_server
    from services.bidex_telegram_quote_parser import configure_bidex_parser
    from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1
    from services.pg_scheduler_engine import get_default_worker
    from services.pg_webhook_engine import WebhookEngineV1

    configure_bidex_parser(DealerQuoteAuthorityEngineV1)
    logger.info("Dealer quote engine initialized")
    logger.info("BidEx parser initialized")

    WebhookEngineV1.register_event_handlers()
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

    try:
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        seed = await PlatformPermissionsEngineV1.ensure_seeded()
        logger.info("Platform permissions seed: %s", seed)
    except Exception:
        logger.warning("Platform permissions seed failed", exc_info=True)

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

    # Background escalation poller (every 60s)
    import asyncio

    async def _escalation_loop() -> None:
        from services.pg_escalation_engine import EscalationEngineV1

        while True:
            try:
                result = await EscalationEngineV1.process_pending()
                if result.get("acted"):
                    logger.info("Escalation acted=%s", result)
            except Exception:
                logger.warning("Escalation loop error", exc_info=True)
            await asyncio.sleep(60)

    escalation_task = asyncio.create_task(_escalation_loop(), name="escalation_loop")

    return StartupContext(
        scheduler=scheduler,
        runner=runner,
        startup=startup,
        diagnostics=diagnostics,
        escalation_task=escalation_task,
    )


async def shutdown_startup(context: StartupContext) -> None:
    from database.session import shutdown_db

    task = getattr(context, "escalation_task", None)
    if task is not None:
        task.cancel()
    await context.scheduler.shutdown()
    if context.runner is not None:
        await context.runner.cleanup()
    await shutdown_db()
