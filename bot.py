import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_HOST, API_PORT, BOT_TOKEN
from auto_vertical_handlers import auto_vertical_router as auto_router
from handlers import router
from middleware.tenant_middleware import TenantMiddleware
from middleware.entry_point_middleware import EntryPointMiddleware
from routers.auto_client_router import router as auto_client_entry_router
from routers.auto_dealer_router import router as auto_dealer_entry_router
from routers.manager_debug_router import router as manager_debug_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.update.middleware(EntryPointMiddleware())
dp.update.middleware(TenantMiddleware())
dp.include_router(auto_client_entry_router)
dp.include_router(auto_dealer_entry_router)
dp.include_router(manager_debug_router)
dp.include_router(auto_router)
dp.include_router(router)


async def main() -> None:
    from api.server import start_api_server
    from database.session import shutdown_db
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
    from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

    diagnostics = await ManagerDeliveryEngineV1.startup_diagnostics()
    logger.info("Manager startup diagnostics: %s", diagnostics)

    manager_id = diagnostics.get("internal_user_id")
    if manager_id:
        logger.info(
            "Auto manager ready: telegram_id=%s uuid=%s roles=%s",
            393792086,
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
    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.shutdown()
        if runner is not None:
            await runner.cleanup()
        await shutdown_db()


if __name__ == "__main__":
    asyncio.run(main())
