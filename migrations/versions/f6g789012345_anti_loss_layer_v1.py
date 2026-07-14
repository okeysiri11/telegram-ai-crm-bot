"""anti_loss_layer_v1

Revision ID: f6g789012345
Revises: f5f678901234
Create Date: 2026-07-14 13:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6g789012345"
down_revision: Union[str, None] = "f5f678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anti_loss_layer_v1_fingerprints",
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("fingerprint_type", sa.String(length=40), nullable=False),
        sa.Column("fingerprint_value", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
            "vertical",
            "fingerprint_type",
            "fingerprint_value",
            name="uq_anti_loss_v1_fingerprint",
        ),
    )
    op.create_index(
        "ix_anti_loss_v1_fp_entity",
        "anti_loss_layer_v1_fingerprints",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_anti_loss_v1_fp_vertical",
        "anti_loss_layer_v1_fingerprints",
        ["vertical"],
    )
    op.create_index(
        "ix_anti_loss_v1_fp_active",
        "anti_loss_layer_v1_fingerprints",
        ["is_active"],
    )

    op.create_table(
        "anti_loss_layer_v1_events",
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("matched_entity_id", sa.UUID(), nullable=True),
        sa.Column("match_type", sa.String(length=40), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("actor_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_anti_loss_v1_events_type",
        "anti_loss_layer_v1_events",
        ["event_type"],
    )
    op.create_index(
        "ix_anti_loss_v1_events_vertical",
        "anti_loss_layer_v1_events",
        ["vertical"],
    )
    op.create_index(
        "ix_anti_loss_v1_events_entity",
        "anti_loss_layer_v1_events",
        ["entity_id"],
    )

    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("phone_normalized", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("vin", sa.String(length=17), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("vehicle_registration", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("agro_product", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("agro_volume", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("agro_location", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("duplicate_of_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("merged_into_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lead_engine_v1_duplicate_of",
        "lead_engine_v1_leads",
        "lead_engine_v1_leads",
        ["duplicate_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lead_engine_v1_merged_into",
        "lead_engine_v1_leads",
        "lead_engine_v1_leads",
        ["merged_into_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_lead_engine_v1_phone_norm", "lead_engine_v1_leads", ["phone_normalized"])
    op.create_index("ix_lead_engine_v1_vin", "lead_engine_v1_leads", ["vin"])
    op.create_index(
        "ix_lead_engine_v1_vehicle_reg",
        "lead_engine_v1_leads",
        ["vehicle_registration"],
    )

    op.execute(
        sa.text(
            "UPDATE lead_engine_v1_leads SET phone_normalized = "
            "regexp_replace(phone, '[^0-9]', '', 'g') "
            "WHERE phone IS NOT NULL AND phone != ''"
        )
    )

    op.add_column(
        "deal_engine_v1_deals",
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "deal_engine_v1_deals",
        sa.Column("duplicate_of_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "deal_engine_v1_deals",
        sa.Column("merged_into_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_deal_engine_v1_duplicate_of",
        "deal_engine_v1_deals",
        "deal_engine_v1_deals",
        ["duplicate_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_deal_engine_v1_merged_into",
        "deal_engine_v1_deals",
        "deal_engine_v1_deals",
        ["merged_into_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_deal_engine_v1_merged_into", "deal_engine_v1_deals", type_="foreignkey")
    op.drop_constraint("fk_deal_engine_v1_duplicate_of", "deal_engine_v1_deals", type_="foreignkey")
    op.drop_column("deal_engine_v1_deals", "merged_into_id")
    op.drop_column("deal_engine_v1_deals", "duplicate_of_id")
    op.drop_column("deal_engine_v1_deals", "is_duplicate")

    op.drop_constraint("fk_lead_engine_v1_merged_into", "lead_engine_v1_leads", type_="foreignkey")
    op.drop_constraint("fk_lead_engine_v1_duplicate_of", "lead_engine_v1_leads", type_="foreignkey")
    op.drop_index("ix_lead_engine_v1_vehicle_reg", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_vin", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_phone_norm", table_name="lead_engine_v1_leads")
    op.drop_column("lead_engine_v1_leads", "merged_into_id")
    op.drop_column("lead_engine_v1_leads", "duplicate_of_id")
    op.drop_column("lead_engine_v1_leads", "is_duplicate")
    op.drop_column("lead_engine_v1_leads", "agro_location")
    op.drop_column("lead_engine_v1_leads", "agro_volume")
    op.drop_column("lead_engine_v1_leads", "agro_product")
    op.drop_column("lead_engine_v1_leads", "vehicle_registration")
    op.drop_column("lead_engine_v1_leads", "vin")
    op.drop_column("lead_engine_v1_leads", "phone_normalized")

    op.drop_index("ix_anti_loss_v1_events_entity", table_name="anti_loss_layer_v1_events")
    op.drop_index("ix_anti_loss_v1_events_vertical", table_name="anti_loss_layer_v1_events")
    op.drop_index("ix_anti_loss_v1_events_type", table_name="anti_loss_layer_v1_events")
    op.drop_table("anti_loss_layer_v1_events")

    op.drop_index("ix_anti_loss_v1_fp_active", table_name="anti_loss_layer_v1_fingerprints")
    op.drop_index("ix_anti_loss_v1_fp_vertical", table_name="anti_loss_layer_v1_fingerprints")
    op.drop_index("ix_anti_loss_v1_fp_entity", table_name="anti_loss_layer_v1_fingerprints")
    op.drop_table("anti_loss_layer_v1_fingerprints")
