# Tenant-scoped query helpers for automatic filtering.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select


def apply_tenant_filter(
    query: Select[Any],
    model: Any,
    tenant_id: uuid.UUID | None,
    *,
    required: bool = True,
) -> Select[Any]:
    if tenant_id is None:
        if required:
            raise ValueError("tenant_id is required for tenant-scoped query")
        return query
    if not hasattr(model, "tenant_id"):
        return query
    return query.where(model.tenant_id == tenant_id)


def tenant_match(entity: Any, tenant_id: uuid.UUID | None) -> bool:
    if tenant_id is None:
        return False
    return getattr(entity, "tenant_id", None) == tenant_id
