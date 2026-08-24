"""Lawyer Operator Desk persistence — Sprint 51.0/51.1 + Lawyer 3.1 CRM cards."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class _ArchiveMixin:
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)


class LegalOpsClient(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_clients"
    __table_args__ = (
        Index("ix_legal_ops_clients_org", "organization_id"),
        Index("ix_legal_ops_clients_tenant", "tenant_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    client_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    avatar_file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(Text(), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    position: Mapped[str | None] = mapped_column(String(256), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    identity_data: Mapped[str | None] = mapped_column(String(256), nullable=True)
    tags: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    contacts: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)


class LegalOpsCase(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_cases"
    __table_args__ = (
        Index("ix_legal_ops_cases_org", "organization_id"),
        Index("ix_legal_ops_cases_client", "client_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    case_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    practice_area: Mapped[str | None] = mapped_column(String(128), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(256), nullable=True)
    timeline: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    case_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    court: Mapped[str | None] = mapped_column(String(256), nullable=True)
    judge: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    participants: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    court_case_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LegalOpsContract(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_contracts"
    __table_args__ = (Index("ix_legal_ops_contracts_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    approval_status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    body: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(256), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(256), nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    signing_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    contract_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LegalOpsDocument(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_documents"
    __table_args__ = (Index("ix_legal_ops_documents_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)


class LegalOpsTask(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_tasks"
    __table_args__ = (Index("ix_legal_ops_tasks_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="task")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assignee: Mapped[str | None] = mapped_column(String(256), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LegalOpsHearing(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_hearings"
    __table_args__ = (Index("ix_legal_ops_hearings_org", "organization_id"),)

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    court_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="scheduled")
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    court_case_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    judge: Mapped[str | None] = mapped_column(String(256), nullable=True)
    room: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hearing_format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    result: Mapped[str | None] = mapped_column(Text(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LegalOpsCalendarEvent(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_calendar_events"
    __table_args__ = (
        Index("ix_legal_ops_cal_org", "organization_id"),
        UniqueConstraint("organization_id", "dedupe_key", name="uq_legal_ops_cal_dedupe"),
        UniqueConstraint("organization_id", "gcal_event_id", name="uq_legal_ops_cal_gcal"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hearing_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    gcal_event_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(64), nullable=False, default="local")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    responsible_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    source_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    external_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)


class LegalOpsActivity(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "legal_ops_activity"
    __table_args__ = (
        Index("ix_legal_ops_activity_org", "organization_id"),
        Index("ix_legal_ops_activity_entity", "entity_type", "entity_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class LegalOpsFile(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_files"
    __table_args__ = (
        Index("ix_legal_ops_files_org", "organization_id"),
        Index("ix_legal_ops_files_entity", "entity_type", "entity_id"),
        Index("ix_legal_ops_files_inbox", "inbox_status"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    file_version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    inbox_status: Mapped[str] = mapped_column(String(32), nullable=False, default="linked")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

class LegalOpsAiAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_ai_analyses"
    __table_args__ = (
        Index("ix_legal_ops_ai_analyses_org", "organization_id"),
        Index("ix_legal_ops_ai_analyses_case", "case_id"),
        Index("ix_legal_ops_ai_analyses_target", "target_type", "target_id"),
    )

    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    workspace_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="analysis")
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    question: Mapped[str | None] = mapped_column(Text(), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sources: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    context_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    provider_meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_tasks: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    created_events: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    created_documents: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class LegalOpsWatchlist(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_watchlist"
    __table_args__ = (
        Index("ix_legal_ops_watchlist_org", "organization_id"),
        Index("ix_legal_ops_watchlist_case", "case_id"),
        Index("ix_legal_ops_watchlist_ext", "external_case_number"),
    )
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="court_case")
    external_case_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="manual_import")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalized_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    automation: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    check_frequency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(512), nullable=True)
    decision_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enforcement_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)



class LegalOpsMonitorChange(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_monitor_changes"
    __table_args__ = (
        Index("ix_legal_ops_monitor_changes_org", "organization_id"),
        Index("ix_legal_ops_monitor_changes_dedupe", "organization_id", "dedupe_key", unique=True),
    )
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    watchlist_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    workflow_status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    old_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    new_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(Text(), nullable=True)
    enforcement_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    suggestions: Mapped[dict[str, Any] | list | None] = mapped_column(JSONB, nullable=True)



class LegalOpsEnforcement(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, _ArchiveMixin, Base):
    __tablename__ = "legal_ops_enforcement"
    __table_args__ = (Index("ix_legal_ops_enforcement_org", "organization_id"),)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    production_number: Mapped[str] = mapped_column(String(128), nullable=False)
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    debtor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    creditor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    executor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class LegalOpsCalendarMapping(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "legal_ops_calendar_mappings"
    __table_args__ = (
        Index("ix_legal_ops_cal_map_internal", "organization_id", "internal_event_id", "provider", unique=True),
        Index("ix_legal_ops_cal_map_external", "organization_id", "external_event_id"),
    )
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    internal_event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="google")
    external_calendar_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    external_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    sync_version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_direction: Mapped[str] = mapped_column(String(32), nullable=False, default="ados_to_google")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class LegalOpsMonitorSettings(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "legal_ops_monitor_settings"
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Kyiv")
    cron_morning: Mapped[str] = mapped_column(String(64), nullable=False, default="0 9 * * *")
    cron_evening: Mapped[str] = mapped_column(String(64), nullable=False, default="0 18 * * *")
    google_sync: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

