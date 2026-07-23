"""Data import engine (module name data_import — `import` is reserved in Python)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataImportEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def import_records(
        self,
        *,
        tenant_id: str,
        source: str,
        records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not source:
            raise ValidationError("source is required")
        rows = records or []
        iid = _id("tn_imp")
        return self.store.tn_imports.save(
            iid,
            {
                "import_id": iid,
                "tenant_id": tenant_id,
                "source": source,
                "record_count": len(rows),
                "records": rows[:100],
                "status": "imported",
                "at": _now(),
            },
        )
