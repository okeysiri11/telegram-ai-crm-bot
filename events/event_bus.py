# Internal async event bus — isolated handlers, structured logging.

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from events.base_event import BaseEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[BaseEvent], Awaitable[None] | None]

_subscribers: dict[str, list[tuple[str, EventHandler]]] = {}


class PlatformEventBus:
    """In-process async pub/sub for platform domain events."""

    @staticmethod
    def subscribe(
        event_type: type[BaseEvent] | str,
        handler: EventHandler,
        *,
        handler_id: str | None = None,
    ) -> str:
        key = event_type if isinstance(event_type, str) else event_type.__name__
        name = handler_id or getattr(handler, "__name__", handler.__class__.__name__)
        bucket = _subscribers.setdefault(key, [])
        bucket[:] = [(hid, fn) for hid, fn in bucket if hid != name]
        bucket.append((name, handler))
        logger.info(
            "platform_event_subscribed",
            extra={"event_type": key, "handler_id": name},
        )
        return name

    @staticmethod
    async def publish(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
        handlers = list(_subscribers.get(event.event_type, []))
        logger.info(
            "platform_event_published",
            extra={
                "event_type": event.event_type,
                "event_id": event.event_id,
                "handler_count": len(handlers),
                "request_number": getattr(event, "request_number", None),
            },
        )
        if not handlers:
            return {"event_type": event.event_type, "handlers": 0, "errors": []}

        tasks = [
            asyncio.create_task(
                PlatformEventBus._invoke_safe(handler_id, handler, event),
                name=f"evt-{event.event_type}-{handler_id}",
            )
            for handler_id, handler in handlers
        ]
        if wait:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [str(r) for r in results if isinstance(r, Exception)]
            return {
                "event_type": event.event_type,
                "handlers": len(handlers),
                "errors": errors,
            }

        for task in tasks:
            task.add_done_callback(PlatformEventBus._log_task_error)
        return {"event_type": event.event_type, "handlers": len(handlers), "errors": []}

    @staticmethod
    async def _invoke_safe(handler_id: str, handler: EventHandler, event: BaseEvent) -> None:
        try:
            result = handler(event)
            if inspect.isawaitable(result):
                await result
            logger.info(
                "platform_event_handler_ok",
                extra={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "handler_id": handler_id,
                },
            )
        except Exception as exc:
            logger.exception(
                "platform_event_handler_failed",
                extra={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "handler_id": handler_id,
                    "error": str(exc),
                },
            )
            raise

    @staticmethod
    def _log_task_error(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.warning(
                "platform_event_handler_task_failed",
                extra={"error": str(exc)},
                exc_info=exc,
            )

    @staticmethod
    def list_subscribers(event_type: str | None = None) -> dict[str, list[str]]:
        if event_type is not None:
            return {event_type: [hid for hid, _ in _subscribers.get(event_type, [])]}
        return {key: [hid for hid, _ in items] for key, items in _subscribers.items()}

    @staticmethod
    def reset_subscribers() -> None:
        _subscribers.clear()


def subscribe(
    event_type: type[BaseEvent] | str,
    handler: EventHandler,
    *,
    handler_id: str | None = None,
) -> str:
    return PlatformEventBus.subscribe(event_type, handler, handler_id=handler_id)


async def publish(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await PlatformEventBus.publish(event, wait=wait)


def reset_subscribers() -> None:
    PlatformEventBus.reset_subscribers()
