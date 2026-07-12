# Public API Gateway v1 — clients, keys, usage logs, rate limits.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ApiClientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class ApiKeyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ApiClient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_gateway_v1_api_clients"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_api_gateway_v1_clients_client_id"),
        Index("ix_api_gateway_v1_clients_status", "status"),
    )

    client_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ApiClientStatus.ACTIVE.value,
        nullable=False,
    )
    permissions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ApiClient client_id={self.client_id} name={self.name}>"


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_gateway_v1_api_keys"
    __table_args__ = (
        Index("ix_api_gateway_v1_keys_client_id", "client_id"),
        Index("ix_api_gateway_v1_keys_prefix", "key_prefix"),
        Index("ix_api_gateway_v1_keys_status", "status"),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_gateway_v1_api_clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ApiKeyStatus.ACTIVE.value,
        nullable=False,
    )
    permissions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ApiKey prefix={self.key_prefix} client={self.client_id}>"


class ApiUsageLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "api_gateway_v1_api_usage_logs"
    __table_args__ = (
        Index("ix_api_gateway_v1_usage_client_id", "client_id"),
        Index("ix_api_gateway_v1_usage_key_id", "key_id"),
        Index("ix_api_gateway_v1_usage_path", "path"),
        Index("ix_api_gateway_v1_usage_created_at", "created_at"),
    )

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_gateway_v1_api_clients.id", ondelete="SET NULL"),
        nullable=True,
    )
    key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_gateway_v1_api_keys.id", ondelete="SET NULL"),
        nullable=True,
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_version: Mapped[str] = mapped_column(String(10), default="v1", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ApiUsageLog {self.method} {self.path} status={self.status_code}>"


class ApiRateLimit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_gateway_v1_api_rate_limits"
    __table_args__ = (
        CheckConstraint("requests_per_minute > 0", name="ck_api_gateway_v1_rl_rpm"),
        CheckConstraint("requests_per_hour > 0", name="ck_api_gateway_v1_rl_rph"),
        Index("ix_api_gateway_v1_rl_client_id", "client_id"),
        Index("ix_api_gateway_v1_rl_endpoint", "endpoint_pattern"),
    )

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_gateway_v1_api_clients.id", ondelete="CASCADE"),
        nullable=True,
    )
    key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_gateway_v1_api_keys.id", ondelete="CASCADE"),
        nullable=True,
    )
    endpoint_pattern: Mapped[str] = mapped_column(String(200), default="*", nullable=False)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    requests_per_hour: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    burst_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ApiRateLimit client={self.client_id} "
            f"pattern={self.endpoint_pattern} rpm={self.requests_per_minute}>"
        )
