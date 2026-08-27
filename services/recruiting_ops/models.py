"""Recruiting Ops durable registry — generic kind + JSONB payload."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from database.base import Base


class RecruitingOpsRecord(Base):
    __tablename__ = "recruiting_ops_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String(128), nullable=False, default="default")
    tenant_id = Column(String(128), nullable=False, default="default")
    kind = Column(String(64), nullable=False)
    status = Column(String(64), nullable=False, default="active")
    payload = Column(JSONB, nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(String(128), nullable=True)
    archive_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    version = Column(Integer, nullable=False, default=1)
