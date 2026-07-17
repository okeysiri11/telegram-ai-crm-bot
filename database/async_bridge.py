# Async bridge — run coroutines from legacy sync callers safely.

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute coroutine from sync code (aiogram handlers prefer await directly)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    if loop.is_running():
        future = asyncio.ensure_future(coro)
        # Fire-and-forget when called from running loop without await.
        return future  # type: ignore[return-value]
    return loop.run_until_complete(coro)


def fire_and_forget(coro: Coroutine[Any, Any, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
