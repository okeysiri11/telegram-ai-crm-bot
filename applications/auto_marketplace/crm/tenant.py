# Tenant scoping for Auto Marketplace Web CRM (does not alter request JSON contracts).

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

DEFAULT_CRM_TENANT = "default"

_crm_tenant: ContextVar[str] = ContextVar("auto_marketplace_crm_tenant", default=DEFAULT_CRM_TENANT)


def normalize_crm_tenant(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_CRM_TENANT
    return text[:128]


def current_crm_tenant() -> str:
    return normalize_crm_tenant(_crm_tenant.get())


def bind_crm_tenant(tenant_id: str) -> Token:
    return _crm_tenant.set(normalize_crm_tenant(tenant_id))


def reset_crm_tenant(token: Token) -> None:
    _crm_tenant.reset(token)


def tenant_from_principal(principal: object) -> str:
    if not isinstance(principal, dict):
        return DEFAULT_CRM_TENANT
    for key in ("tenant_id", "organization_id", "org_id", "company_id"):
        value = principal.get(key)
        if value not in (None, ""):
            return normalize_crm_tenant(value)
    return DEFAULT_CRM_TENANT


def tenant_from_request(request: Any) -> str:
    principal = request.get("principal") if hasattr(request, "get") else None
    tid = tenant_from_principal(principal)
    if tid != DEFAULT_CRM_TENANT:
        return tid
    headers = getattr(request, "headers", {})
    query = getattr(request, "query", {})
    header = None
    if headers:
        header = headers.get("X-Tenant-Id") or headers.get("X-Organization-Id")
    if not header and query:
        header = query.get("tenant_id")
    if header:
        return normalize_crm_tenant(header)
    return DEFAULT_CRM_TENANT
