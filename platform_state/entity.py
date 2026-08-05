"""Canonical business entity model — Sprint 34.2D (TD-54 aligned)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from platform_state.models import utcnow


@dataclass
class CanonicalEntity:
    """
    Base model for every shared business entity.
    Clients must never invent parallel shapes — use this (or VersionEngine.apply).
    """

    id: str
    entity_type: str
    version: int = 1
    created_at: str = field(default_factory=lambda: utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: utcnow().isoformat())
    created_by: str | None = None
    updated_by: str | None = None
    workspace_id: str | None = None
    tenant_id: str | None = None
    source_client: str | None = None
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deleted_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        entity_type: str,
        data: dict[str, Any] | None = None,
        entity_id: str | None = None,
        created_by: str | None = None,
        workspace_id: str | None = None,
        tenant_id: str | None = None,
        source_client: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalEntity:
        now = utcnow().isoformat()
        return cls(
            id=entity_id or str(uuid.uuid4()),
            entity_type=entity_type,
            version=1,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            source_client=source_client,
            change_id=str(uuid.uuid4()),
            metadata=dict(metadata or {}),
            data=dict(data or {}),
        )

    def bump(
        self,
        *,
        updated_by: str | None = None,
        source_client: str | None = None,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        soft_delete: bool = False,
    ) -> CanonicalEntity:
        self.version += 1
        self.updated_at = utcnow().isoformat()
        self.change_id = str(uuid.uuid4())
        if updated_by is not None:
            self.updated_by = updated_by
        if source_client is not None:
            self.source_client = source_client
        if data is not None:
            self.data = {**self.data, **data}
        if metadata is not None:
            self.metadata = {**self.metadata, **metadata}
        if soft_delete:
            self.deleted_at = self.updated_at
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CanonicalEntity:
        return cls(
            id=str(raw["id"]),
            entity_type=str(raw["entity_type"]),
            version=int(raw.get("version") or 1),
            created_at=str(raw.get("created_at") or utcnow().isoformat()),
            updated_at=str(raw.get("updated_at") or utcnow().isoformat()),
            created_by=raw.get("created_by"),
            updated_by=raw.get("updated_by"),
            workspace_id=raw.get("workspace_id"),
            tenant_id=raw.get("tenant_id"),
            source_client=raw.get("source_client"),
            change_id=str(raw.get("change_id") or uuid.uuid4()),
            deleted_at=raw.get("deleted_at"),
            metadata=dict(raw.get("metadata") or {}),
            data=dict(raw.get("data") or {}),
        )


# Typed aliases for catalog clarity (same runtime type).
ENTITY_TYPES: tuple[str, ...] = (
    "user",
    "company",
    "crm",
    "deal",
    "lead",
    "task",
    "calendar_event",
    "file",
    "document",
    "chat",
    "conversation",
    "notification",
    "project",
    "knowledge",
    "agent",
)
