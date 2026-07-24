
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class HeatmapViz:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def render(self) -> dict[str, Any]:
        cells = [
            {
                "capability_key": i["key"],
                "domain": i["domain"],
                "maturity_level": i["maturity_level"],
                "heat": round(i["maturity_level"] / 5, 2),
            }
            for i in self.registry.list_all()
        ]
        if not cells:
            raise ValidationError("no capabilities for heatmap")
        vid = _id("ebc_vheat")
        record = {"viz_id": vid, "kind": "heatmap", "cells": cells, "rendered_at": _now()}
        self.store.ebc_visualizations.save(vid, record)
        return record
