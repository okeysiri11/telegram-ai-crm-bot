# Management API authentication — JWT and API keys only.

from __future__ import annotations

from platform_identity.identity_service import identity_service
from platform_identity.models import Principal


async def authenticate_management_request(request) -> Principal:
    """Require JWT (Authorization: Bearer) or X-API-Key — no trusted Telegram headers."""
    return await identity_service.authenticate_request(request)


def attach_principal_to_context(ctx, principal: Principal) -> None:
    ctx.actor_telegram_id = principal.telegram_id
    ctx.principal_id = principal.principal_id
    ctx.auth_method = principal.auth_method.value if principal.auth_method else None
