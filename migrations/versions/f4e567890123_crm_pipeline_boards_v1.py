"""crm_pipeline_boards_v1

Revision ID: f4e567890123
Revises: f3d456789012
Create Date: 2026-07-14 12:30:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f4e567890123"
down_revision: Union[str, None] = "f3d456789012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AUTO_STAGES = [
    ("NEW", "Новый", "Новий", 0),
    ("CONTACTED", "Связались", "Зв'язалися", 1),
    ("QUALIFIED", "Квалифицирован", "Кваліфікований", 2),
    ("OFFER_SENT", "Предложение отправлено", "Пропозицію надіслано", 3),
    ("NEGOTIATION", "Переговоры", "Переговори", 4),
    ("PAYMENT_PENDING", "Ожидание оплаты", "Очікування оплати", 5),
    ("WON", "Выигран", "Виграно", 6),
    ("LOST", "Проигран", "Програно", 7),
]

AGRO_STAGES = [
    ("NEW", "Новый", "Новий", 0),
    ("MATCHING", "Подбор", "Підбір", 1),
    ("NEGOTIATION", "Переговоры", "Переговори", 2),
    ("CONTRACT_PREPARATION", "Подготовка контракта", "Підготовка контракту", 3),
    ("LOGISTICS", "Логистика", "Логістика", 4),
    ("PAYMENT_PENDING", "Ожидание оплаты", "Очікування оплати", 5),
    ("CLOSED", "Закрыт", "Закрито", 6),
    ("LOST", "Проигран", "Програно", 7),
]


def upgrade() -> None:
    op.create_table(
        "crm_pipeline_boards_v1_stages",
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("stage_code", sa.String(length=50), nullable=False),
        sa.Column("stage_name_ru", sa.String(length=120), nullable=False),
        sa.Column("stage_name_uk", sa.String(length=120), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vertical", "stage_code", name="uq_crm_pipeline_v1_stage_vertical_code"),
    )
    op.create_index(
        "ix_crm_pipeline_v1_stages_vertical",
        "crm_pipeline_boards_v1_stages",
        ["vertical"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_stages_order",
        "crm_pipeline_boards_v1_stages",
        ["vertical", "order_index"],
    )

    op.create_table(
        "crm_pipeline_boards_v1_transitions",
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("previous_stage", sa.String(length=50), nullable=True),
        sa.Column("new_stage", sa.String(length=50), nullable=False),
        sa.Column("moved_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "moved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("pipeline_stage_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_stage_id"],
            ["crm_pipeline_boards_v1_stages.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_entity",
        "crm_pipeline_boards_v1_transitions",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_vertical",
        "crm_pipeline_boards_v1_transitions",
        ["vertical"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_prev",
        "crm_pipeline_boards_v1_transitions",
        ["previous_stage"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_new",
        "crm_pipeline_boards_v1_transitions",
        ["new_stage"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_moved_by",
        "crm_pipeline_boards_v1_transitions",
        ["moved_by"],
    )
    op.create_index(
        "ix_crm_pipeline_v1_trans_moved_at",
        "crm_pipeline_boards_v1_transitions",
        ["moved_at"],
    )

    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("pipeline_stage", sa.String(length=50), nullable=False, server_default="NEW"),
    )
    op.create_index(
        "ix_lead_engine_v1_pipeline_stage",
        "lead_engine_v1_leads",
        ["pipeline_stage"],
    )
    op.execute(
        sa.text(
            "UPDATE lead_engine_v1_leads SET pipeline_stage = status "
            "WHERE status IN ('NEW','CONTACTED','QUALIFIED','NEGOTIATION','PAYMENT_PENDING','WON','LOST')"
        )
    )

    op.add_column(
        "deal_engine_v1_deals",
        sa.Column("pipeline_stage", sa.String(length=50), nullable=False, server_default="NEW"),
    )
    op.create_index(
        "ix_deal_engine_v1_pipeline_stage",
        "deal_engine_v1_deals",
        ["pipeline_stage"],
    )

    stages_table = sa.table(
        "crm_pipeline_boards_v1_stages",
        sa.column("id", sa.UUID()),
        sa.column("vertical", sa.String()),
        sa.column("stage_code", sa.String()),
        sa.column("stage_name_ru", sa.String()),
        sa.column("stage_name_uk", sa.String()),
        sa.column("order_index", sa.Integer()),
    )
    rows = []
    for code, ru, uk, order_idx in AUTO_STAGES:
        rows.append({
            "id": uuid.uuid4(),
            "vertical": "auto",
            "stage_code": code,
            "stage_name_ru": ru,
            "stage_name_uk": uk,
            "order_index": order_idx,
        })
    for code, ru, uk, order_idx in AGRO_STAGES:
        rows.append({
            "id": uuid.uuid4(),
            "vertical": "agro",
            "stage_code": code,
            "stage_name_ru": ru,
            "stage_name_uk": uk,
            "order_index": order_idx,
        })
    op.bulk_insert(stages_table, rows)


def downgrade() -> None:
    op.drop_index("ix_deal_engine_v1_pipeline_stage", table_name="deal_engine_v1_deals")
    op.drop_column("deal_engine_v1_deals", "pipeline_stage")
    op.drop_index("ix_lead_engine_v1_pipeline_stage", table_name="lead_engine_v1_leads")
    op.drop_column("lead_engine_v1_leads", "pipeline_stage")

    op.drop_index("ix_crm_pipeline_v1_trans_moved_at", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_index("ix_crm_pipeline_v1_trans_moved_by", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_index("ix_crm_pipeline_v1_trans_new", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_index("ix_crm_pipeline_v1_trans_prev", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_index("ix_crm_pipeline_v1_trans_vertical", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_index("ix_crm_pipeline_v1_trans_entity", table_name="crm_pipeline_boards_v1_transitions")
    op.drop_table("crm_pipeline_boards_v1_transitions")

    op.drop_index("ix_crm_pipeline_v1_stages_order", table_name="crm_pipeline_boards_v1_stages")
    op.drop_index("ix_crm_pipeline_v1_stages_vertical", table_name="crm_pipeline_boards_v1_stages")
    op.drop_table("crm_pipeline_boards_v1_stages")
