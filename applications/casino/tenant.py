"""Tenant scoping for the Casino vertical."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

DEFAULT_CASINO_TENANT = "default"

_casino_tenant: ContextVar[str] = ContextVar("casino_tenant", default=DEFAULT_CASINO_TENANT)


def normalize_casino_tenant(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_CASINO_TENANT
    return text[:128]


def current_casino_tenant() -> str:
    return normalize_casino_tenant(_casino_tenant.get())


def bind_casino_tenant(tenant_id: str) -> Token:
    return _casino_tenant.set(normalize_casino_tenant(tenant_id))


def reset_casino_tenant(token: Token) -> None:
    _casino_tenant.reset(token)


def tenant_from_principal(principal: object) -> str:
    if not isinstance(principal, dict):
        return DEFAULT_CASINO_TENANT
    for key in ("tenant_id", "organization_id", "org_id", "company_id"):
        value = principal.get(key)
        if value not in (None, ""):
            return normalize_casino_tenant(value)
    return DEFAULT_CASINO_TENANT


def tenant_from_request(request: Any) -> str:
    principal = request.get("principal") if hasattr(request, "get") else None
    tid = tenant_from_principal(principal)
    if tid != DEFAULT_CASINO_TENANT:
        return tid
    headers = getattr(request, "headers", {}) or {}
    query = getattr(request, "query", {}) or {}
    header = headers.get("X-Tenant-Id") or headers.get("X-Organization-Id")
    if not header:
        header = query.get("tenant_id")
    if header:
        return normalize_casino_tenant(header)
    return DEFAULT_CASINO_TENANT


def player_id_from_principal(principal: object, *, fallback: str = "anonymous") -> str:
    if not isinstance(principal, dict):
        return fallback[:64]
    for key in ("sub", "user_id", "player_id", "session_id", "token"):
        value = principal.get(key)
        if value not in (None, ""):
            return str(value)[:64]
    return fallback[:64]
