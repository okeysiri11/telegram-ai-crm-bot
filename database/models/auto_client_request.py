# Auto Client — client request records (search / sell / listing).

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AutoClientRequestType(str, enum.Enum):
    AUTO_SEARCH = "AUTO_SEARCH"
    AUTO_SELL = "AUTO_SELL"
    AUTO_LISTING = "AUTO_LISTING"
    AUTO_MANAGER_CALLBACK = "AUTO_MANAGER_CALLBACK"


class AutoClientRequestStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class AutoClientRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_client_requests_v1"
    __table_args__ = (
        Index("ix_auto_client_requests_v1_number", "request_number", unique=True),
        Index("ix_auto_client_requests_v1_client", "client_telegram_id"),
        Index("ix_auto_client_requests_v1_manager", "manager_id"),
        Index("ix_auto_client_requests_v1_status", "status"),
        Index("ix_auto_client_requests_v1_type", "request_type"),
    )

    request_number: Mapped[str] = mapped_column(String(32), nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=AutoClientRequestStatus.NEW.value,
        nullable=False,
    )
    client_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    client_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
