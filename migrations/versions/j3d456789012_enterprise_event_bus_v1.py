"""Enterprise Event Bus tables — Sprint 36.1.

Revision ID: j3d456789012
Revises: i2c345678901
Create Date: 2026-08-03 14:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "j3d456789012"
down_revision: Union[str, None] = "i2c345678901"
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
        "event_store",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=256), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="platform"),
        sa.Column("topic", sa.String(length=64), nullable=False, server_default="platform"),
        sa.Column("source_service", sa.String(length=128), nullable=False),
        sa.Column("target_service", sa.String(length=128), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("causation_id", sa.String(length=64), nullable=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=True),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("signature", sa.String(length=128), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("security_context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("event_version", sa.String(length=32), nullable=False, server_default="1.0"),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        *_ts_cols(),
        sa.UniqueConstraint("event_key", name="uq_event_store_event_key"),
    )
    op.create_index("ix_event_store_event_key", "event_store", ["event_key"])
    op.create_index("ix_event_store_topic", "event_store", ["topic"])
    op.create_index("ix_event_store_event_type", "event_store", ["event_type"])
    op.create_index("ix_event_store_tenant", "event_store", ["tenant_id"])
    op.create_index("ix_event_store_occurred_at", "event_store", ["occurred_at"])

    op.create_table(
        "event_topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subscriber_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("name", name="uq_event_topics_name"),
    )

    op.create_table(
        "event_subscribers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("subscription_key", sa.String(length=64), nullable=False),
        sa.Column("subscriber_id", sa.String(length=128), nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=256), nullable=True),
        sa.Column("event_filter", sa.String(length=256), nullable=True),
        sa.Column("priority_min", sa.String(length=32), nullable=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=True),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("regex", sa.String(length=256), nullable=True),
        sa.Column("wildcard", sa.String(length=256), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("meta_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("subscription_key", name="uq_event_subscribers_subscription_key"),
    )
    op.create_index("ix_event_subscribers_subscriber", "event_subscribers", ["subscriber_id"])
    op.create_index("ix_event_subscribers_topic", "event_subscribers", ["topic"])

    op.create_table(
        "event_delivery",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("delivery_key", sa.String(length=64), nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False),
        sa.Column("subscriber_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("delivery_key", name="uq_event_delivery_delivery_key"),
    )
    op.create_index("ix_event_delivery_event_key", "event_delivery", ["event_key"])
    op.create_index("ix_event_delivery_status", "event_delivery", ["status"])

    op.create_table(
        "dead_letter_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("dlq_key", sa.String(length=64), nullable=False),
        sa.Column("event_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("subscriber_id", sa.String(length=128), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retried", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_ts_cols(),
        sa.UniqueConstraint("dlq_key", name="uq_dead_letter_queue_dlq_key"),
    )
    op.create_index("ix_dead_letter_queue_created", "dead_letter_queue", ["created_at"])

    op.create_table(
        "event_statistics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metrics_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_event_statistics_bucket", "event_statistics", ["bucket_start"])

    op.create_table(
        "event_replay",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("replay_key", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("filter_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("replayed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("replay_key", name="uq_event_replay_replay_key"),
    )
    op.create_index("ix_event_replay_created", "event_replay", ["created_at"])


def downgrade() -> None:
    op.drop_table("event_replay")
    op.drop_table("event_statistics")
    op.drop_table("dead_letter_queue")
    op.drop_table("event_delivery")
    op.drop_table("event_subscribers")
    op.drop_table("event_topics")
    op.drop_table("event_store")
