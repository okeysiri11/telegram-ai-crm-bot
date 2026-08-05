"""Voice Command Center ORM — Sprint 36.6."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class VoiceSessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_voice_sessions_session_key"),
        Index("ix_voice_sessions_status", "status"),
        Index("ix_voice_sessions_principal", "principal"),
    )

    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    principal: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    profile_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="push_to_talk")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cipher_hint: Mapped[str] = mapped_column(String(64), nullable=False, default="aes-gcm-demo")
    storage_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class VoiceCommandRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_commands"
    __table_args__ = (
        Index("ix_voice_commands_session_key", "session_key"),
        Index("ix_voice_commands_intent", "intent"),
    )

    command_key: Mapped[str] = mapped_column(String(64), nullable=False)
    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False, default="")
    intent: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    entities_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk: Mapped[str] = mapped_column(String(32), nullable=False, default="safe")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="parsed")
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class VoiceHistoryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_history"
    __table_args__ = (
        Index("ix_voice_history_session_key", "session_key"),
        Index("ix_voice_history_action", "action"),
    )

    history_key: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    command_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    principal: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class VoiceDeviceRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_devices"
    __table_args__ = (
        UniqueConstraint("device_key", name="uq_voice_devices_device_key"),
        Index("ix_voice_devices_owner", "owner"),
    )

    device_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="microphone")
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capabilities_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class VoiceProfileRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_profiles"
    __table_args__ = (
        UniqueConstraint("profile_key", name="uq_voice_profiles_profile_key"),
        Index("ix_voice_profiles_principal", "principal"),
    )

    profile_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    principal: Mapped[str] = mapped_column(String(128), nullable=False)
    locale: Mapped[str] = mapped_column(String(32), nullable=False, default="en-US")
    wake_word: Mapped[str] = mapped_column(String(128), nullable=False, default="hey ados")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="push_to_talk")
    preferred_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="whisper")
    confirm_dangerous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    roles_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class VoiceStatisticsRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "voice_statistics"
    __table_args__ = (Index("ix_voice_statistics_metric_key", "metric_key"),)

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
