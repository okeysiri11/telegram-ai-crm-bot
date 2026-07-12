"""automotive_ai_copilot_v1

Revision ID: 6a2a99ff8267
Revises: a88d4ccbb6ad
Create Date: 2026-07-12 23:34:47.764225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "6a2a99ff8267"
down_revision: Union[str, None] = "a88d4ccbb6ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automotive_ai_copilot_v1_ai_predictions",
        sa.Column("prediction_type", sa.String(length=30), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("predicted_value", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_automotive_ai_copilot_v1_pred_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_pred_model",
        "automotive_ai_copilot_v1_ai_predictions",
        ["model_version"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_pred_type",
        "automotive_ai_copilot_v1_ai_predictions",
        ["prediction_type"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_pred_vehicle",
        "automotive_ai_copilot_v1_ai_predictions",
        ["vehicle_id"],
        unique=False,
    )
    op.create_table(
        "automotive_ai_copilot_v1_ai_recommendations",
        sa.Column("recommendation_type", sa.String(length=30), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommended_value", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("input_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_automotive_ai_copilot_v1_rec_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_rec_model",
        "automotive_ai_copilot_v1_ai_recommendations",
        ["model_version"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_rec_type",
        "automotive_ai_copilot_v1_ai_recommendations",
        ["recommendation_type"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_rec_vehicle",
        "automotive_ai_copilot_v1_ai_recommendations",
        ["vehicle_id"],
        unique=False,
    )
    op.create_table(
        "automotive_ai_copilot_v1_ai_decisions",
        sa.Column("recommendation_id", sa.UUID(), nullable=True),
        sa.Column("prediction_id", sa.UUID(), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("decision_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("decided_by", sa.BigInteger(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_value", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
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
            ["prediction_id"],
            ["automotive_ai_copilot_v1_ai_predictions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["automotive_ai_copilot_v1_ai_recommendations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_dec_status",
        "automotive_ai_copilot_v1_ai_decisions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_dec_vehicle",
        "automotive_ai_copilot_v1_ai_decisions",
        ["vehicle_id"],
        unique=False,
    )
    op.create_table(
        "automotive_ai_copilot_v1_ai_feedback",
        sa.Column("recommendation_id", sa.UUID(), nullable=True),
        sa.Column("decision_id", sa.UUID(), nullable=True),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("submitted_by", sa.BigInteger(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["automotive_ai_copilot_v1_ai_decisions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["automotive_ai_copilot_v1_ai_recommendations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_fb_decision",
        "automotive_ai_copilot_v1_ai_feedback",
        ["decision_id"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_fb_model",
        "automotive_ai_copilot_v1_ai_feedback",
        ["model_version"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_ai_copilot_v1_fb_recommendation",
        "automotive_ai_copilot_v1_ai_feedback",
        ["recommendation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_automotive_ai_copilot_v1_fb_recommendation",
        table_name="automotive_ai_copilot_v1_ai_feedback",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_fb_model",
        table_name="automotive_ai_copilot_v1_ai_feedback",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_fb_decision",
        table_name="automotive_ai_copilot_v1_ai_feedback",
    )
    op.drop_table("automotive_ai_copilot_v1_ai_feedback")
    op.drop_index(
        "ix_automotive_ai_copilot_v1_dec_vehicle",
        table_name="automotive_ai_copilot_v1_ai_decisions",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_dec_status",
        table_name="automotive_ai_copilot_v1_ai_decisions",
    )
    op.drop_table("automotive_ai_copilot_v1_ai_decisions")
    op.drop_index(
        "ix_automotive_ai_copilot_v1_rec_vehicle",
        table_name="automotive_ai_copilot_v1_ai_recommendations",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_rec_type",
        table_name="automotive_ai_copilot_v1_ai_recommendations",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_rec_model",
        table_name="automotive_ai_copilot_v1_ai_recommendations",
    )
    op.drop_table("automotive_ai_copilot_v1_ai_recommendations")
    op.drop_index(
        "ix_automotive_ai_copilot_v1_pred_vehicle",
        table_name="automotive_ai_copilot_v1_ai_predictions",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_pred_type",
        table_name="automotive_ai_copilot_v1_ai_predictions",
    )
    op.drop_index(
        "ix_automotive_ai_copilot_v1_pred_model",
        table_name="automotive_ai_copilot_v1_ai_predictions",
    )
    op.drop_table("automotive_ai_copilot_v1_ai_predictions")
