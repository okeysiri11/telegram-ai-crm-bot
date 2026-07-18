# assignment_scores ORM — smart assignment learning dataset.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AssignmentScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assignment_scores"
    __table_args__ = (
        Index("ix_assignment_scores_segment", "segment"),
        Index("ix_assignment_scores_strategy", "strategy"),
        Index("ix_assignment_scores_manager_pool_id", "manager_pool_id"),
        Index("ix_assignment_scores_request_id", "request_id"),
        Index("ix_assignment_scores_assignment_time", "assignment_time"),
        Index("ix_assignment_scores_completed", "completed"),
    )

    request_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    request_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manager_pool_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    manager_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    manager_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    segment: Mapped[str] = mapped_column(String(32), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, default="SMART")
    assignment_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
