"""feature_flag_engine_v1

Revision ID: b8f2c91d4e03
Revises: a1a256785aa5
Create Date: 2026-07-13 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b8f2c91d4e03"
down_revision: Union[str, None] = "a1a256785aa5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_flag_engine_v1_feature_flags",
        sa.Column("flag_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("default_variant", sa.String(length=32), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
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
        sa.UniqueConstraint("flag_key", name="uq_feature_flag_engine_v1_flags_key"),
    )
    op.create_index(
        "ix_feature_flag_engine_v1_flags_status",
        "feature_flag_engine_v1_feature_flags",
        ["status"],
        unique=False,
    )
    op.create_table(
        "feature_flag_engine_v1_feature_assignments",
        sa.Column("flag_id", sa.UUID(), nullable=False),
        sa.Column("assignment_type", sa.String(length=20), nullable=False),
        sa.Column("target_key", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("rollout_percentage", sa.Integer(), nullable=True),
        sa.Column("variant", sa.String(length=32), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["flag_id"],
            ["feature_flag_engine_v1_feature_flags.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "flag_id",
            "assignment_type",
            "target_key",
            name="uq_feature_flag_engine_v1_assignments",
        ),
    )
    op.create_index(
        "ix_feature_flag_engine_v1_assign_flag",
        "feature_flag_engine_v1_feature_assignments",
        ["flag_id"],
        unique=False,
    )
    op.create_index(
        "ix_feature_flag_engine_v1_assign_target",
        "feature_flag_engine_v1_feature_assignments",
        ["target_key"],
        unique=False,
    )
    op.create_index(
        "ix_feature_flag_engine_v1_assign_type",
        "feature_flag_engine_v1_feature_assignments",
        ["assignment_type"],
        unique=False,
    )
    op.create_table(
        "feature_flag_engine_v1_feature_history",
        sa.Column("flag_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["flag_id"],
            ["feature_flag_engine_v1_feature_flags.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feature_flag_engine_v1_hist_action",
        "feature_flag_engine_v1_feature_history",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_feature_flag_engine_v1_hist_flag",
        "feature_flag_engine_v1_feature_history",
        ["flag_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_feature_flag_engine_v1_hist_flag",
        table_name="feature_flag_engine_v1_feature_history",
    )
    op.drop_index(
        "ix_feature_flag_engine_v1_hist_action",
        table_name="feature_flag_engine_v1_feature_history",
    )
    op.drop_table("feature_flag_engine_v1_feature_history")
    op.drop_index(
        "ix_feature_flag_engine_v1_assign_type",
        table_name="feature_flag_engine_v1_feature_assignments",
    )
    op.drop_index(
        "ix_feature_flag_engine_v1_assign_target",
        table_name="feature_flag_engine_v1_feature_assignments",
    )
    op.drop_index(
        "ix_feature_flag_engine_v1_assign_flag",
        table_name="feature_flag_engine_v1_feature_assignments",
    )
    op.drop_table("feature_flag_engine_v1_feature_assignments")
    op.drop_index(
        "ix_feature_flag_engine_v1_flags_status",
        table_name="feature_flag_engine_v1_feature_flags",
    )
    op.drop_table("feature_flag_engine_v1_feature_flags")
