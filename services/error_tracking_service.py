# ErrorTrackingService — capture handler errors to PostgreSQL and Sentry without blocking.

from __future__ import annotations

import asyncio
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from config import SENTRY_DSN
from database.models.observability_engine import ErrorSeverity
from database.session import get_session
from repositories.observability_engine_repository import ErrorEventRepository

logger = logging.getLogger(__name__)

SOURCE_TELEGRAM = "telegram_handler"
_sentry_initialized = False


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("error_tracking background task failed: %s", exc, exc_info=exc)


class ErrorTrackingService:
    """Fire-and-forget error capture — never blocks Telegram handlers."""

    @staticmethod
    def _enqueue(coro) -> None:
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(coro)
            task.add_done_callback(_log_task_error)
        except RuntimeError:
            try:
                asyncio.run(coro)
            except Exception:
                logger.warning("error_tracking sync fallback failed", exc_info=True)

    @staticmethod
    def ensure_sentry() -> bool:
        global _sentry_initialized
        if _sentry_initialized:
            return bool(SENTRY_DSN)
        if not SENTRY_DSN:
            return False
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
            _sentry_initialized = True
            logger.info("Sentry initialized for error tracking")
            return True
        except Exception:
            logger.warning("Sentry init failed", exc_info=True)
            return False

    @staticmethod
    async def extract_context(
        event: TelegramObject,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = data or {}
        ctx: dict[str, Any] = {
            "telegram_id": None,
            "vertical": None,
            "fsm_state": None,
            "request_id": None,
            "handler_name": None,
            "payload": None,
        }

        user = data.get("event_from_user")
        if user is not None:
            ctx["telegram_id"] = user.id

        payload: str | None = None
        if isinstance(event, Message):
            payload = event.text or event.caption
            if user is None and event.from_user:
                ctx["telegram_id"] = event.from_user.id
        elif isinstance(event, CallbackQuery):
            payload = event.data
            if user is None and event.from_user:
                ctx["telegram_id"] = event.from_user.id
        elif isinstance(event, Update):
            if event.message:
                payload = event.message.text or event.message.caption
                if event.message.from_user:
                    ctx["telegram_id"] = event.message.from_user.id
            elif event.callback_query:
                payload = event.callback_query.data
                if event.callback_query.from_user:
                    ctx["telegram_id"] = event.callback_query.from_user.id
        else:
            data_val = getattr(event, "data", None)
            if isinstance(data_val, str):
                payload = data_val
            else:
                text_val = getattr(event, "text", None)
                cap_val = getattr(event, "caption", None)
                if isinstance(text_val, str):
                    payload = text_val
                elif isinstance(cap_val, str):
                    payload = cap_val
            if ctx["telegram_id"] is None and getattr(event, "from_user", None) is not None:
                ctx["telegram_id"] = event.from_user.id

        ctx["payload"] = payload

        handler = data.get("handler")
        if handler is not None:
            callback = getattr(handler, "callback", handler)
            ctx["handler_name"] = getattr(callback, "__name__", None) or repr(handler)

        state = data.get("state")
        state_data: dict[str, Any] = {}
        if state is not None:
            try:
                ctx["fsm_state"] = await state.get_state()
                state_data = await state.get_data()
            except Exception:
                logger.debug("Failed to read FSM state for error context", exc_info=True)

        ctx["request_id"] = (
            state_data.get("request_id")
            or state_data.get("request_number")
            or state_data.get("created_number")
        )

        tenant_ctx = data.get("tenant_ctx")
        vertical = None
        if tenant_ctx is not None:
            vertical = getattr(tenant_ctx, "vertical", None) or getattr(tenant_ctx, "vertical_code", None)
        ctx["vertical"] = (
            vertical
            or state_data.get("vertical")
            or state_data.get("flow_type")
            or data.get("vertical")
        )

        return ctx

    @staticmethod
    async def _persist_error(
        *,
        error_type: str,
        message: str,
        stack_trace: str | None,
        context: dict[str, Any],
        severity: str = ErrorSeverity.ERROR.value,
    ) -> None:
        try:
            async with get_session() as session:
                await ErrorEventRepository(session).record(
                    source=SOURCE_TELEGRAM,
                    error_type=error_type,
                    message=message[:8000],
                    stack_trace=stack_trace,
                    context=context,
                    severity=severity,
                    recorded_at=datetime.now(timezone.utc),
                )
        except Exception:
            logger.warning("Failed to persist error event", exc_info=True)

    @staticmethod
    def _report_sentry(
        exc: BaseException | None,
        *,
        error_type: str,
        message: str,
        context: dict[str, Any],
    ) -> None:
        if not SENTRY_DSN:
            return
        try:
            ErrorTrackingService.ensure_sentry()
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                scope.set_tag("source", SOURCE_TELEGRAM)
                for key in ("telegram_id", "vertical", "fsm_state", "request_id", "handler_name"):
                    value = context.get(key)
                    if value is not None:
                        scope.set_tag(key, str(value))
                scope.set_extra("payload", context.get("payload"))
                scope.set_extra("context", context)
                if exc is not None:
                    sentry_sdk.capture_exception(exc)
                else:
                    sentry_sdk.capture_message(message, level="error")
        except Exception:
            logger.warning("Sentry report failed", exc_info=True)

    @staticmethod
    async def _capture(
        exc: BaseException | None,
        *,
        error_type: str | None = None,
        message: str | None = None,
        stack_trace: str | None = None,
        context: dict[str, Any] | None = None,
        severity: str = ErrorSeverity.ERROR.value,
    ) -> None:
        if exc is not None:
            error_type = error_type or type(exc).__name__
            message = message or str(exc) or error_type
            stack_trace = stack_trace or "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
        else:
            error_type = error_type or "Error"
            message = message or "Unknown error"
            stack_trace = stack_trace or traceback.format_exc()

        safe_context = context or {}
        logger.error(
            "tracked_error type=%s telegram_id=%s vertical=%s handler=%s",
            error_type,
            safe_context.get("telegram_id"),
            safe_context.get("vertical"),
            safe_context.get("handler_name"),
            exc_info=exc,
        )
        await ErrorTrackingService._persist_error(
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            context=safe_context,
            severity=severity,
        )
        ErrorTrackingService._report_sentry(
            exc,
            error_type=error_type,
            message=message,
            context=safe_context,
        )

    @staticmethod
    async def capture_exception(
        exc: BaseException,
        *,
        event: TelegramObject | None = None,
        data: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        severity: str = ErrorSeverity.ERROR.value,
    ) -> None:
        merged = dict(context or {})
        if event is not None:
            extracted = await ErrorTrackingService.extract_context(event, data)
            merged = {**extracted, **{k: v for k, v in merged.items() if v is not None}}
        ErrorTrackingService._enqueue(
            ErrorTrackingService._capture(exc, context=merged, severity=severity)
        )

    @staticmethod
    async def track_error(
        *,
        message: str,
        error_type: str = "TrackedError",
        event: TelegramObject | None = None,
        data: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        severity: str = ErrorSeverity.ERROR.value,
    ) -> None:
        merged = dict(context or {})
        if event is not None:
            extracted = await ErrorTrackingService.extract_context(event, data)
            merged = {**extracted, **{k: v for k, v in merged.items() if v is not None}}
        ErrorTrackingService._enqueue(
            ErrorTrackingService._capture(
                None,
                error_type=error_type,
                message=message,
                stack_trace="".join(traceback.format_stack(sys._getframe(1))),
                context=merged,
                severity=severity,
            )
        )

    @staticmethod
    async def track_from_handler(
        exc: BaseException,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> None:
        await ErrorTrackingService.capture_exception(exc, event=event, data=data)


error_tracking_service = ErrorTrackingService()
