# Application entry point — bootstrap, startup, polling lifecycle.

from __future__ import annotations

import asyncio
import logging

from bootstrap import bot, build_dispatcher, create_fsm_storage
from startup import run_startup, shutdown_startup

logger = logging.getLogger(__name__)


async def main() -> None:
    storage, redis_storage = await create_fsm_storage()
    dp = build_dispatcher(storage)
    context = await run_startup()

    try:
        await dp.start_polling(bot)
    finally:
        await shutdown_startup(context, redis_storage=redis_storage)


if __name__ == "__main__":
    asyncio.run(main())
