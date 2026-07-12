"""automotive_cost_engine_v1_full

Revision ID: f7a3c2d81e04
Revises: c4e8a1b92f03
Create Date: 2026-07-12 22:45:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a3c2d81e04"
down_revision: Union[str, None] = "c4e8a1b92f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("vehicle.cost.updated", "Emit or subscribe to vehicle cost updated events"),
    ("vehicle.margin.updated", "Emit or subscribe to vehicle margin updated events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
}


def _seed_cost_event_permissions() -> None:
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
    op.rename_table(
        "automotive_cost_v1_margin_rules",
        "automotive_cost_v1_vehicle_margin_rules",
    )
    op.drop_index(
        "ix_automotive_cost_v1_mr_is_active",
        table_name="automotive_cost_v1_vehicle_margin_rules",
    )
    op.drop_index(
        "ix_automotive_cost_v1_mr_priority",
        table_name="automotive_cost_v1_vehicle_margin_rules",
    )
    op.create_index(
        "ix_automotive_cost_v1_vmr_is_active",
        "automotive_cost_v1_vehicle_margin_rules",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_cost_v1_vmr_priority",
        "automotive_cost_v1_vehicle_margin_rules",
        ["priority"],
        unique=False,
    )

    op.drop_constraint(
        "ck_automotive_cost_v1_vc_total",
        "automotive_cost_v1_vehicle_costs",
        type_="check",
    )
    op.alter_column(
        "automotive_cost_v1_vehicle_costs",
        "subtotal_amount",
        new_column_name="total_cost",
    )
    op.alter_column(
        "automotive_cost_v1_vehicle_costs",
        "total_amount",
        new_column_name="target_price",
    )
    op.drop_column("automotive_cost_v1_vehicle_costs", "purchase_amount")
    op.add_column(
        "automotive_cost_v1_vehicle_costs",
        sa.Column("roi_percent", sa.Numeric(precision=8, scale=4), nullable=True),
    )
    op.create_check_constraint(
        "ck_automotive_cost_v1_vc_total_cost",
        "automotive_cost_v1_vehicle_costs",
        "total_cost >= 0",
    )

    op.drop_index(
        "ix_automotive_cost_v1_ci_vehicle_cost_id",
        table_name="automotive_cost_v1_cost_items",
    )
    op.drop_index(
        "ix_automotive_cost_v1_ci_item_type",
        table_name="automotive_cost_v1_cost_items",
    )
    op.drop_table("automotive_cost_v1_cost_items")

    op.create_table(
        "automotive_cost_v1_vehicle_cost_items",
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("cost_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_cost_v1_vci_vehicle_id",
        "automotive_cost_v1_vehicle_cost_items",
        ["vehicle_id"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_cost_v1_vci_cost_type",
        "automotive_cost_v1_vehicle_cost_items",
        ["cost_type"],
        unique=False,
    )

    _seed_cost_event_permissions()


def downgrade() -> None:
    op.drop_index(
        "ix_automotive_cost_v1_vci_cost_type",
        table_name="automotive_cost_v1_vehicle_cost_items",
    )
    op.drop_index(
        "ix_automotive_cost_v1_vci_vehicle_id",
        table_name="automotive_cost_v1_vehicle_cost_items",
    )
    op.drop_table("automotive_cost_v1_vehicle_cost_items")

    op.create_table(
        "automotive_cost_v1_cost_items",
        sa.Column("vehicle_cost_id", sa.UUID(), nullable=False),
        sa.Column("item_type", sa.String(length=30), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("is_calculated", sa.Boolean(), nullable=False),
        sa.Column("calculation_method", sa.String(length=50), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["vehicle_cost_id"],
            ["automotive_cost_v1_vehicle_costs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_cost_v1_ci_item_type",
        "automotive_cost_v1_cost_items",
        ["item_type"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_cost_v1_ci_vehicle_cost_id",
        "automotive_cost_v1_cost_items",
        ["vehicle_cost_id"],
        unique=False,
    )

    op.drop_constraint(
        "ck_automotive_cost_v1_vc_total_cost",
        "automotive_cost_v1_vehicle_costs",
        type_="check",
    )
    op.drop_column("automotive_cost_v1_vehicle_costs", "roi_percent")
    op.add_column(
        "automotive_cost_v1_vehicle_costs",
        sa.Column("purchase_amount", sa.Numeric(precision=20, scale=2), nullable=False, server_default="0"),
    )
    op.alter_column(
        "automotive_cost_v1_vehicle_costs",
        "target_price",
        new_column_name="total_amount",
    )
    op.alter_column(
        "automotive_cost_v1_vehicle_costs",
        "total_cost",
        new_column_name="subtotal_amount",
    )
    op.create_check_constraint(
        "ck_automotive_cost_v1_vc_total",
        "automotive_cost_v1_vehicle_costs",
        "total_amount >= 0",
    )

    op.drop_index(
        "ix_automotive_cost_v1_vmr_priority",
        table_name="automotive_cost_v1_vehicle_margin_rules",
    )
    op.drop_index(
        "ix_automotive_cost_v1_vmr_is_active",
        table_name="automotive_cost_v1_vehicle_margin_rules",
    )
    op.create_index(
        "ix_automotive_cost_v1_mr_priority",
        "automotive_cost_v1_vehicle_margin_rules",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_cost_v1_mr_is_active",
        "automotive_cost_v1_vehicle_margin_rules",
        ["is_active"],
        unique=False,
    )
    op.rename_table(
        "automotive_cost_v1_vehicle_margin_rules",
        "automotive_cost_v1_margin_rules",
    )

    codes = [code for code, _ in NEW_EVENT_PERMISSIONS]
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code = ANY(:codes))"
        ),
        {"codes": codes},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
