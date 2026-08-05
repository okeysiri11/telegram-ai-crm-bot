# User identity links — Sprint 34.2A.
# One users.id may have many provider links (telegram, email, phone, google, isam).

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin, VersionMixin

if TYPE_CHECKING:
    from database.models.users import User


class UserIdentityLink(UUIDPrimaryKeyMixin, VersionMixin, Base):
    __tablename__ = "user_identity_links"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_user_identity_links_provider_external"),
        Index("ix_user_identity_links_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="identity_links")
