# Tenant-scoped query helpers — Sprint 30.0 hardening (TD-58).

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import Select

logger = logging.getLogger(__name__)


class TenantIsolationError(ValueError):
    """Raised when a tenant-scoped query would run without a tenant filter."""


def require_tenant_id(tenant_id: uuid.UUID | None, *, context: str = "query") -> uuid.UUID:
    if tenant_id is None:
        raise TenantIsolationError(f"tenant_id is required for tenant-scoped {context}")
    return tenant_id


def apply_tenant_filter(
    query: Select[Any],
    model: Any,
    tenant_id: uuid.UUID | None,
    *,
    required: bool | None = None,
) -> Select[Any]:
    """Apply ``model.tenant_id == tenant_id``.

    When ``required`` is None, uses ConfigurationCenter ``require_tenant_filter``
    (default True). Cross-tenant admin tools may pass ``required=False`` explicitly.
    """
    if required is None:
        try:
            from platform_configuration.configuration_center import configuration_center

            required = configuration_center.settings.security.require_tenant_filter
        except Exception:
            required = True

    if tenant_id is None:
        if required:
            raise TenantIsolationError("tenant_id is required for tenant-scoped query")
        logger.warning("tenant_filter_bypassed model=%s", getattr(model, "__name__", model))
        return query
    if not hasattr(model, "tenant_id"):
        return query
    return query.where(model.tenant_id == tenant_id)


def tenant_match(entity: Any, tenant_id: uuid.UUID | None) -> bool:
    if tenant_id is None:
        return False
    return getattr(entity, "tenant_id", None) == tenant_id


def assert_entity_tenant(entity: Any, tenant_id: uuid.UUID | None) -> None:
    if not tenant_match(entity, tenant_id):
        raise TenantIsolationError("entity does not belong to the active tenant")
