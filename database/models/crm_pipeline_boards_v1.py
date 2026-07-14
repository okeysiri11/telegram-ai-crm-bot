# CRM Pipeline Boards v1 — vertical stage config and transition log.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class CrmPipelineEntityType(str, enum.Enum):
    LEAD = "lead"
    DEAL = "deal"


CRM_PIPELINE_VERTICALS = frozenset({"auto", "agro"})

AUTO_PIPELINE_STAGES = (
    "NEW",
    "CONTACTED",
    "QUALIFIED",
    "OFFER_SENT",
    "NEGOTIATION",
    "PAYMENT_PENDING",
    "WON",
    "LOST",
)

AGRO_PIPELINE_STAGES = (
    "NEW",
    "MATCHING",
    "NEGOTIATION",
    "CONTRACT_PREPARATION",
    "LOGISTICS",
    "PAYMENT_PENDING",
    "CLOSED",
    "LOST",
)

AUTO_WIN_STAGES = frozenset({"WON"})
AGRO_WIN_STAGES = frozenset({"CLOSED"})
PIPELINE_LOST_STAGES = frozenset({"LOST"})


class CrmPipelineBoardStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "crm_pipeline_boards_v1_stages"
    __table_args__ = (
        UniqueConstraint("vertical", "stage_code", name="uq_crm_pipeline_v1_stage_vertical_code"),
        Index("ix_crm_pipeline_v1_stages_vertical", "vertical"),
        Index("ix_crm_pipeline_v1_stages_order", "vertical", "order_index"),
    )

    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    stage_code: Mapped[str] = mapped_column(String(50), nullable=False)
    stage_name_ru: Mapped[str] = mapped_column(String(120), nullable=False)
    stage_name_uk: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CrmPipelineBoardTransition(CreatedAtMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "crm_pipeline_boards_v1_transitions"
    __table_args__ = (
        Index("ix_crm_pipeline_v1_trans_entity", "entity_type", "entity_id"),
        Index("ix_crm_pipeline_v1_trans_vertical", "vertical"),
        Index("ix_crm_pipeline_v1_trans_prev", "previous_stage"),
        Index("ix_crm_pipeline_v1_trans_new", "new_stage"),
        Index("ix_crm_pipeline_v1_trans_moved_by", "moved_by"),
        Index("ix_crm_pipeline_v1_trans_moved_at", "moved_at"),
    )

    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    previous_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_stage: Mapped[str] = mapped_column(String(50), nullable=False)

    moved_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    pipeline_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crm_pipeline_boards_v1_stages.id", ondelete="SET NULL"),
        nullable=True,
    )
