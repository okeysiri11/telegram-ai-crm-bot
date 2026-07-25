"""Concierge Registry — exactly one Concierge per organization."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.exceptions import ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ConciergeRegistry:
    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def get_for_organization(self, organization_id: str) -> dict[str, Any] | None:
        for item in self.store.concierge_registry.list_all():
            if item.get("organization_id") == organization_id:
                return item
        return None

    def register(self, concierge: dict[str, Any]) -> dict[str, Any]:
        org_id = (concierge.get("organization_id") or "").strip()
        if not org_id:
            raise ValidationError("organization_id is required")
        existing = self.get_for_organization(org_id)
        if existing:
            raise ValidationError(
                f"Organization already has a Concierge ({existing['concierge_id']}). Only one Concierge is allowed."
            )
        cid = concierge.get("concierge_id") or _id("concierge")
        record = {
            **concierge,
            "concierge_id": cid,
            "organization_id": org_id,
            "kind": "enterprise_ai_concierge",
            "not_an_ai_agent": True,
            "independent_from_ai_agents": True,
            "coordinates_specialists": True,
            "specialists_execute_work": True,
            "registry": "platform_builder_concierge_registry",
            "lifecycle": "registered",
            "linked_to_organization": True,
            "registered_at": _now(),
            "source": "concierge_builder",
            "sprint": "28.3",
        }
        self.store.concierge_registry.save(cid, record)
        self.store.organization_links.save(
            org_id,
            {
                "organization_id": org_id,
                "concierge_id": cid,
                "linked_at": _now(),
            },
        )
        return record

    def list_all(self) -> dict[str, Any]:
        items = self.store.concierge_registry.list_all()
        return {
            "count": len(items),
            "items": items,
            "registry": "platform_builder_concierge_registry",
            "rule": "exactly_one_per_organization",
        }
