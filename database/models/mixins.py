# Shared SQLAlchemy mixins for PostgreSQL models.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class VersionColumnsMixin:
    """
    TD-54 / Sprint 35.1 — optimistic versioning columns without tenant_id.

    Many tables already own a UUID `tenant_id` FK; this mixin never collides with it.
    Use this on every persistent business entity.
    """

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    change_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_client: Mapped[str | None] = mapped_column(String(32), nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class VersionMixin(VersionColumnsMixin):
    """
    Canonical name for TD-54 versioning (Sprint 34.2D / completed 35.1).

    Alias of VersionColumnsMixin — does not add String tenant_id (avoids UUID tenant collisions).
    Tenant scope remains on entity-owned `tenant_id` columns where present.
    """


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
