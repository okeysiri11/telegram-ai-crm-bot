"""AGRO Production 1.0 — durable ops registry.

Architectural decision (documented in docs/SPRINT_AGRO_PRODUCTION_1_0_RESULT.md):
one generic JSONB-backed table with a `kind` discriminator instead of ~20 typed
tables. Entity shapes for the new AGRO desk are still evolving; the registry
keeps tenant isolation, restart durability and archiving with a single
reversible migration. Typed columns can be promoted later without breaking the
API contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class AgroOpsRecord(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agro_ops_records"
    __table_args__ = (
        Index("ix_agro_ops_records_org_kind", "organization_id", "kind"),
        Index("ix_agro_ops_records_tenant", "tenant_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
