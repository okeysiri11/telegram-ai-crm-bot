# Document Engine v1 — templates, documents, versions, signatures.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentType(str, enum.Enum):
    INVOICE = "INVOICE"
    PURCHASE_CONTRACT = "PURCHASE_CONTRACT"
    SALES_CONTRACT = "SALES_CONTRACT"
    CUSTOMS_DOCUMENT = "CUSTOMS_DOCUMENT"
    DELIVERY_ACT = "DELIVERY_ACT"


class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    SIGNED = "SIGNED"
    VOID = "VOID"


class SignerRole(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    WITNESS = "WITNESS"
    AUTHORIZED_REP = "AUTHORIZED_REP"
    CUSTOMS_OFFICER = "CUSTOMS_OFFICER"


class DocumentTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_engine_v1_document_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_document_engine_v1_templates_code"),
        Index("ix_document_engine_v1_templates_type", "document_type"),
        Index("ix_document_engine_v1_templates_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    default_variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DocumentTemplate code={self.code} type={self.document_type}>"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_engine_v1_documents"
    __table_args__ = (
        UniqueConstraint(
            "reference_number",
            name="uq_document_engine_v1_documents_reference_number",
        ),
        Index("ix_document_engine_v1_documents_type", "document_type"),
        Index("ix_document_engine_v1_documents_status", "status"),
        Index("ix_document_engine_v1_documents_entity", "entity_type", "entity_id"),
    )

    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_engine_v1_document_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.DRAFT.value,
        nullable=False,
    )
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Document ref={self.reference_number} "
            f"type={self.document_type} status={self.status}>"
        )


class DocumentVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "document_engine_v1_document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_engine_v1_versions_doc_version",
        ),
        Index("ix_document_engine_v1_versions_document_id", "document_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_engine_v1_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    generated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<DocumentVersion doc={self.document_id} v={self.version_number}>"


class DocumentSignature(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "document_engine_v1_document_signatures"
    __table_args__ = (
        Index("ix_document_engine_v1_signatures_document_id", "document_id"),
        Index("ix_document_engine_v1_signatures_version_id", "version_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_engine_v1_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_engine_v1_document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    signer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    signer_role: Mapped[str] = mapped_column(String(30), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    signature_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signed_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DocumentSignature doc={self.document_id} "
            f"signer={self.signer_name} role={self.signer_role}>"
        )
