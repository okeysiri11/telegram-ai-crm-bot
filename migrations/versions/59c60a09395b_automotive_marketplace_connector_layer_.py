"""automotive_marketplace_connector_layer_v1

Revision ID: 59c60a09395b
Revises: 187d936210b5
Create Date: 2026-07-12 23:01:08.147381

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "59c60a09395b"
down_revision: Union[str, None] = "187d936210b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("vehicle.import.started", "Emit or subscribe to vehicle import started events"),
    ("vehicle.import.completed", "Emit or subscribe to vehicle import completed events"),
    ("vehicle.price.changed", "Emit or subscribe to vehicle price changed events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
}


def _seed_marketplace_event_permissions() -> None:
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
                continue
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
        "automotive_marketplace_v1_connector_credentials",
        sa.Column("connector_type", sa.String(length=30), nullable=False),
        sa.Column("api_key", sa.String(length=512), nullable=True),
        sa.Column("api_secret", sa.String(length=512), nullable=True),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.UniqueConstraint(
            "connector_type",
            name="uq_automotive_marketplace_v1_credentials_connector_type",
        ),
    )
    op.create_index(
        "ix_automotive_marketplace_v1_cred_is_active",
        "automotive_marketplace_v1_connector_credentials",
        ["is_active"],
        unique=False,
    )
    op.create_table(
        "automotive_marketplace_v1_vehicle_import_jobs",
        sa.Column("connector_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", sa.BigInteger(), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("images_synced", sa.Integer(), nullable=False),
        sa.Column("price_changes", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_marketplace_v1_job_connector",
        "automotive_marketplace_v1_vehicle_import_jobs",
        ["connector_type"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_marketplace_v1_job_scheduled_at",
        "automotive_marketplace_v1_vehicle_import_jobs",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_marketplace_v1_job_status",
        "automotive_marketplace_v1_vehicle_import_jobs",
        ["status"],
        unique=False,
    )
    op.create_table(
        "automotive_marketplace_v1_vehicle_import_logs",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("vin", sa.String(length=50), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("old_price", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("new_price", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["automotive_marketplace_v1_vehicle_import_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_marketplace_v1_log_action",
        "automotive_marketplace_v1_vehicle_import_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_marketplace_v1_log_job_id",
        "automotive_marketplace_v1_vehicle_import_logs",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_marketplace_v1_log_vin",
        "automotive_marketplace_v1_vehicle_import_logs",
        ["vin"],
        unique=False,
    )
    _seed_marketplace_event_permissions()


def downgrade() -> None:
    op.drop_index(
        "ix_automotive_marketplace_v1_log_vin",
        table_name="automotive_marketplace_v1_vehicle_import_logs",
    )
    op.drop_index(
        "ix_automotive_marketplace_v1_log_job_id",
        table_name="automotive_marketplace_v1_vehicle_import_logs",
    )
    op.drop_index(
        "ix_automotive_marketplace_v1_log_action",
        table_name="automotive_marketplace_v1_vehicle_import_logs",
    )
    op.drop_table("automotive_marketplace_v1_vehicle_import_logs")
    op.drop_index(
        "ix_automotive_marketplace_v1_job_status",
        table_name="automotive_marketplace_v1_vehicle_import_jobs",
    )
    op.drop_index(
        "ix_automotive_marketplace_v1_job_scheduled_at",
        table_name="automotive_marketplace_v1_vehicle_import_jobs",
    )
    op.drop_index(
        "ix_automotive_marketplace_v1_job_connector",
        table_name="automotive_marketplace_v1_vehicle_import_jobs",
    )
    op.drop_table("automotive_marketplace_v1_vehicle_import_jobs")
    op.drop_index(
        "ix_automotive_marketplace_v1_cred_is_active",
        table_name="automotive_marketplace_v1_connector_credentials",
    )
    op.drop_table("automotive_marketplace_v1_connector_credentials")
