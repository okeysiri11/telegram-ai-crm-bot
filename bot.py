import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import API_HOST, API_PORT, BOT_TOKEN
from handlers import router
from middleware.tenant_middleware import TenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.update.middleware(TenantMiddleware())
dp.include_router(router)


async def main() -> None:
    from api.server import start_api_server
    from database.session import shutdown_db
    from services.pg_scheduler_engine import get_default_worker
    from services.pg_webhook_engine import WebhookEngineV1

    WebhookEngineV1.register_event_handlers()
    scheduler = get_default_worker()
    await scheduler.start()
    runner = await start_api_server(host=API_HOST, port=API_PORT)
    logger.info(
        "API server listening on http://%s:%s/health (liveness/readiness enabled)",
        API_HOST,
        API_PORT,
    )
    from services.production_readiness_suite import ProductionReadinessSuite

    startup = await ProductionReadinessSuite.validate_startup()
    logger.info(
        "Production readiness startup: status=%s ready=%s",
        startup.get("status"),
        startup.get("ready"),
    )
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
        await runner.cleanup()
        await shutdown_db()


if __name__ == "__main__":
    asyncio.run(main())
