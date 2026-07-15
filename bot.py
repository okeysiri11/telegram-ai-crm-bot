# Backward-compatible public API and legacy entry point.

from __future__ import annotations

import asyncio

from bootstrap import bot, build_dispatcher, close_fsm_storage, create_fsm_storage
from main import main

__all__ = ["bot", "build_dispatcher", "close_fsm_storage", "create_fsm_storage", "main"]

if __name__ == "__main__":
    asyncio.run(main())
