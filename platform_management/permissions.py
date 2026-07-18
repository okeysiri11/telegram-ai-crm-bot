# Management API permissions — JWT/API-key authentication + role enforcement.

from __future__ import annotations

import enum
import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web

from platform_identity.exceptions import AuthenticationError
from platform_management.auth import attach_principal_to_context, authenticate_management_request
from platform_management.exceptions import ManagementPermissionError
from platform_management.management_context import ManagementContext
from platform_management.response_models import error_response

logger = logging.getLogger(__name__)

Handler = Callable[[web.Request, ManagementContext], Awaitable[web.Response]]


class ManagementRole(str, enum.Enum):
    READ_ONLY = "readonly"
    ADMINISTRATOR = "administrator"
    OWNER = "owner"


_ROLE_RANK = {
    ManagementRole.READ_ONLY: 0,
    ManagementRole.ADMINISTRATOR: 1,
    ManagementRole.OWNER: 2,
}


async def resolve_role(telegram_id: int | None) -> ManagementRole:
    from platform_identity.identity_service import identity_service

    return await identity_service.resolve_management_role(telegram_id=telegram_id)


def role_allows(actor_role: ManagementRole, required: ManagementRole) -> bool:
    return _ROLE_RANK[actor_role] >= _ROLE_RANK[required]


def require_role(required: ManagementRole) -> Callable[[Handler], Handler]:
    """Decorator — authenticates via JWT or API key, then enforces role."""

    def decorator(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapper(request: web.Request) -> web.Response:
            from platform_management.management_service import management_service

            ctx = ManagementContext.from_request(request, role=required.value)
            try:
                principal = await authenticate_management_request(request)
                request["principal"] = principal
                attach_principal_to_context(ctx, principal)

                actor_role = await resolve_role(ctx.actor_telegram_id)
                ctx.role = actor_role.value
                if not role_allows(actor_role, required):
                    raise ManagementPermissionError(
                        f"Role {actor_role.value} cannot access endpoint requiring {required.value}"
                    )
                response = await handler(request, ctx)
                await management_service.log_request(ctx, status=response.status)
                return response
            except AuthenticationError as exc:
                await management_service.log_request(ctx, status=401, error=str(exc))
                return error_response(str(exc), request_id=ctx.request_id, status=401)
            except ManagementPermissionError as exc:
                await management_service.log_request(ctx, status=403, error=str(exc))
                return error_response(str(exc), request_id=ctx.request_id, status=403)
            except Exception as exc:
                logger.exception("management_handler_failed path=%s", request.path)
                await management_service.log_request(ctx, status=500, error=str(exc))
                return error_response(str(exc), request_id=ctx.request_id, status=500)

        return wrapper

    return decorator
