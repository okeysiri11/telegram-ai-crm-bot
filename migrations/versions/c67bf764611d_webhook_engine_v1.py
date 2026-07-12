"""webhook_engine_v1

Revision ID: c67bf764611d
Revises: c445e3eba5e8
Create Date: 2026-07-12 23:51:07.614580

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c67bf764611d"
down_revision: Union[str, None] = "c445e3eba5e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("vehicle.imported", "Emit or subscribe to vehicle imported events"),
    ("payment.completed", "Emit or subscribe to payment completed events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ACCOUNTANT": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
}


def _seed_webhook_event_permissions() -> None:
    bind = op.get_bind()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in NEW_EVENT_PERMISSIONS:
        existing = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if existing:
            permission_ids[code] = existing[0]
            continue
        permission_id = uuid.uuid4()
        bind.execute(
            permissions_table.insert().values(
                id=permission_id,
                code=code,
                description=description,
            )
        )
        permission_ids[code] = permission_id

    for role_code, permission_codes in NEW_ROLE_PERMISSIONS.items():
        role_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": role_code},
        ).first()
        if not role_row:
            continue
        role_id = role_row[0]
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                perm_row = bind.execute(
                    sa.text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": permission_code},
                ).first()
                if not perm_row:
                    continue
                permission_id = perm_row[0]
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).first()
            if exists:
                continue
            bind.execute(
                role_permissions_table.insert().values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def upgrade() -> None:
    op.create_table(
        "webhook_engine_v1_webhook_subscriptions",
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_url", sa.String(length=512), nullable=False),
        sa.Column("secret", sa.String(length=128), nullable=False),
        sa.Column("event_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("event_version", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_engine_v1_sub_owner",
        "webhook_engine_v1_webhook_subscriptions",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_sub_status",
        "webhook_engine_v1_webhook_subscriptions",
        ["status"],
        unique=False,
    )
    op.create_table(
        "webhook_engine_v1_webhook_deliveries",
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("source_event_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_version", sa.String(length=10), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("signature", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["webhook_engine_v1_webhook_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_engine_v1_del_event_type",
        "webhook_engine_v1_webhook_deliveries",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_del_source_event",
        "webhook_engine_v1_webhook_deliveries",
        ["source_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_del_status",
        "webhook_engine_v1_webhook_deliveries",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_del_subscription",
        "webhook_engine_v1_webhook_deliveries",
        ["subscription_id"],
        unique=False,
    )
    op.create_table(
        "webhook_engine_v1_webhook_failures",
        sa.Column("delivery_id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["webhook_engine_v1_webhook_deliveries.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["webhook_engine_v1_webhook_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_engine_v1_fail_delivery",
        "webhook_engine_v1_webhook_failures",
        ["delivery_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_fail_subscription",
        "webhook_engine_v1_webhook_failures",
        ["subscription_id"],
        unique=False,
    )
    op.create_table(
        "webhook_engine_v1_webhook_retries",
        sa.Column("delivery_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["webhook_engine_v1_webhook_deliveries.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_engine_v1_retry_delivery",
        "webhook_engine_v1_webhook_retries",
        ["delivery_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_retry_scheduled",
        "webhook_engine_v1_webhook_retries",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_engine_v1_retry_status",
        "webhook_engine_v1_webhook_retries",
        ["status"],
        unique=False,
    )
    _seed_webhook_event_permissions()


def downgrade() -> None:
    op.drop_index(
        "ix_webhook_engine_v1_retry_status",
        table_name="webhook_engine_v1_webhook_retries",
    )
    op.drop_index(
        "ix_webhook_engine_v1_retry_scheduled",
        table_name="webhook_engine_v1_webhook_retries",
    )
    op.drop_index(
        "ix_webhook_engine_v1_retry_delivery",
        table_name="webhook_engine_v1_webhook_retries",
    )
    op.drop_table("webhook_engine_v1_webhook_retries")
    op.drop_index(
        "ix_webhook_engine_v1_fail_subscription",
        table_name="webhook_engine_v1_webhook_failures",
    )
    op.drop_index(
        "ix_webhook_engine_v1_fail_delivery",
        table_name="webhook_engine_v1_webhook_failures",
    )
    op.drop_table("webhook_engine_v1_webhook_failures")
    op.drop_index(
        "ix_webhook_engine_v1_del_subscription",
        table_name="webhook_engine_v1_webhook_deliveries",
    )
    op.drop_index(
        "ix_webhook_engine_v1_del_status",
        table_name="webhook_engine_v1_webhook_deliveries",
    )
    op.drop_index(
        "ix_webhook_engine_v1_del_source_event",
        table_name="webhook_engine_v1_webhook_deliveries",
    )
    op.drop_index(
        "ix_webhook_engine_v1_del_event_type",
        table_name="webhook_engine_v1_webhook_deliveries",
    )
    op.drop_table("webhook_engine_v1_webhook_deliveries")
    op.drop_index(
        "ix_webhook_engine_v1_sub_status",
        table_name="webhook_engine_v1_webhook_subscriptions",
    )
    op.drop_index(
        "ix_webhook_engine_v1_sub_owner",
        table_name="webhook_engine_v1_webhook_subscriptions",
    )
    op.drop_table("webhook_engine_v1_webhook_subscriptions")
