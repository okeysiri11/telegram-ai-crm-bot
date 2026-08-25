"""Casino API middleware — Bearer gate for mutations; tenant bind."""

from __future__ import annotations

from aiohttp import web

from applications.casino.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CasinoError,
    DuplicateSettlementError,
    InsufficientChipsError,
    NotFoundError,
    ValidationError,
)
from applications.casino.tenant import bind_casino_tenant, tenant_from_request
from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

_WRITE = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_PROTECTED_GET_SUFFIXES = ("/wallet", "/ledger")


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


def error_response(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)


def _is_casino_path(path: str) -> bool:
    return path.startswith("/api/casino/")


def _requires_auth(request: web.Request) -> bool:
    if not _is_casino_path(request.path):
        return False
    if request.method in _WRITE:
        return True
    return request.path.endswith(_PROTECTED_GET_SUFFIXES)


@web.middleware
async def casino_auth_middleware(request: web.Request, handler):
    if request.method == "OPTIONS" or not _is_casino_path(request.path):
        return await handler(request)
    auth_header = request.headers.get("Authorization")
    principal = await platform_bridge.authenticate_request(auth_header)
    request["principal"] = principal
    bind_casino_tenant(tenant_from_request(request))
    if _requires_auth(request):
        if not isinstance(principal, dict) or not principal.get("authenticated"):
            return error_response("Authentication required", status=401)
    return await handler(request)


@web.middleware
async def casino_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except AuthenticationError as exc:
        return error_response(str(exc), status=401)
    except AuthorizationError as exc:
        return error_response(str(exc), status=403)
    except InsufficientChipsError as exc:
        return error_response(str(exc), status=400)
    except DuplicateSettlementError as exc:
        return error_response(str(exc), status=409)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
    except ValueError as exc:
        return error_response(str(exc), status=400)
    except CasinoError as exc:
        return error_response(str(exc), status=400)
