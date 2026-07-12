import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import API_HOST, API_PORT, BOT_TOKEN
from handlers import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def main() -> None:
    from api.server import start_api_server
    from database.session import shutdown_db

    runner = await start_api_server(host=API_HOST, port=API_PORT)
    logger.info("API server listening on http://%s:%s/system/db-health", API_HOST, API_PORT)
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await shutdown_db()


if __name__ == "__main__":
    asyncio.run(main())
