"""Voice Command Center tables — Sprint 36.6.

Revision ID: p9j012345678
Revises: o8i901234567
Create Date: 2026-08-03 20:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "p9j012345678"
down_revision: Union[str, None] = "o8i901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "voice_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("principal", sa.String(128), nullable=False, server_default="system"),
        sa.Column("profile_key", sa.String(64), nullable=True),
        sa.Column("device_key", sa.String(64), nullable=True),
        sa.Column("mode", sa.String(32), nullable=False, server_default="push_to_talk"),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("provider_id", sa.String(64), nullable=True),
        sa.Column("encrypted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("cipher_hint", sa.String(64), nullable=False, server_default="aes-gcm-demo"),
        sa.Column("storage_token", sa.Text(), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_voice_sessions_session_key"),
    )
    op.create_index("ix_voice_sessions_status", "voice_sessions", ["status"])
    op.create_index("ix_voice_sessions_principal", "voice_sessions", ["principal"])

    op.create_table(
        "voice_commands",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("command_key", sa.String(64), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False, server_default=""),
        sa.Column("intent", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("entities_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("risk", sa.String(32), nullable=False, server_default="safe"),
        sa.Column("status", sa.String(32), nullable=False, server_default="parsed"),
        sa.Column("result_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("approved_by", sa.String(128), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_voice_commands_session_key", "voice_commands", ["session_key"])
    op.create_index("ix_voice_commands_intent", "voice_commands", ["intent"])

    op.create_table(
        "voice_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("history_key", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("command_key", sa.String(64), nullable=True),
        sa.Column("principal", sa.String(128), nullable=True),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_voice_history_session_key", "voice_history", ["session_key"])
    op.create_index("ix_voice_history_action", "voice_history", ["action"])

    op.create_table(
        "voice_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("device_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False, server_default="microphone"),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("capabilities_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("online", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("device_key", name="uq_voice_devices_device_key"),
    )
    op.create_index("ix_voice_devices_owner", "voice_devices", ["owner"])

    op.create_table(
        "voice_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("principal", sa.String(128), nullable=False),
        sa.Column("locale", sa.String(32), nullable=False, server_default="en-US"),
        sa.Column("wake_word", sa.String(128), nullable=False, server_default="hey ados"),
        sa.Column("mode", sa.String(32), nullable=False, server_default="push_to_talk"),
        sa.Column("preferred_provider", sa.String(64), nullable=False, server_default="whisper"),
        sa.Column("confirm_dangerous", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("roles_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("profile_key", name="uq_voice_profiles_profile_key"),
    )
    op.create_index("ix_voice_profiles_principal", "voice_profiles", ["principal"])

    op.create_table(
        "voice_statistics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_voice_statistics_metric_key", "voice_statistics", ["metric_key"])


def downgrade() -> None:
    for table in (
        "voice_statistics",
        "voice_profiles",
        "voice_devices",
        "voice_history",
        "voice_commands",
        "voice_sessions",
    ):
        op.drop_table(table)
