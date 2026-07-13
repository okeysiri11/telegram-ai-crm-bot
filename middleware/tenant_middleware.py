# Aiogram middleware — inject tenant context into handler data.

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services.tenant_context import ActiveTenantContext, TenantContextService


class TenantMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            ctx = await TenantContextService.resolve_for_user(user.id)
            data["tenant_ctx"] = ctx
            if ctx is not None:
                data["tenant_id"] = ctx.tenant_id
                data["company_id"] = ctx.company_id
        return await handler(event, data)
