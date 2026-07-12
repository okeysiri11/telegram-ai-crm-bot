# Document Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.document_engine import (
    Document,
    DocumentSignature,
    DocumentStatus,
    DocumentTemplate,
    DocumentType,
    DocumentVersion,
    SignerRole,
)


class DocumentTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        code: str,
        name: str,
        document_type: str,
        content_template: str,
        default_variables: dict | None = None,
        is_active: bool = True,
        description: str | None = None,
        **extra: Any,
    ) -> DocumentTemplate:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if document_type not in {t.value for t in DocumentType}:
            raise ValueError(f"Invalid document_type: {document_type}")

        template = DocumentTemplate(
            code=code,
            name=name,
            document_type=document_type,
            content_template=content_template,
            default_variables=default_variables,
            is_active=is_active,
            description=description,
        )
        self._session.add(template)
        await self._session.flush()
        return template

    async def get_by_code(self, code: str) -> DocumentTemplate | None:
        result = await self._session.execute(
            select(DocumentTemplate).where(DocumentTemplate.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, template_id: uuid.UUID) -> DocumentTemplate | None:
        result = await self._session.execute(
            select(DocumentTemplate).where(DocumentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_by_type(
        self,
        document_type: str,
        *,
        active_only: bool = True,
    ) -> list[DocumentTemplate]:
        query = select(DocumentTemplate).where(
            DocumentTemplate.document_type == document_type
        )
        if active_only:
            query = query.where(DocumentTemplate.is_active.is_(True))
        result = await self._session.execute(
            query.order_by(DocumentTemplate.name.asc())
        )
        return list(result.scalars().all())

    async def list_all(self, *, active_only: bool = True) -> list[DocumentTemplate]:
        query = select(DocumentTemplate)
        if active_only:
            query = query.where(DocumentTemplate.is_active.is_(True))
        result = await self._session.execute(
            query.order_by(DocumentTemplate.document_type.asc(), DocumentTemplate.name.asc())
        )
        return list(result.scalars().all())


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        document_type: str,
        title: str,
        reference_number: str,
        template_id: uuid.UUID | None = None,
        status: str = DocumentStatus.DRAFT.value,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> Document:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if document_type not in {t.value for t in DocumentType}:
            raise ValueError(f"Invalid document_type: {document_type}")
        if status not in {s.value for s in DocumentStatus}:
            raise ValueError(f"Invalid status: {status}")

        document = Document(
            template_id=template_id,
            document_type=document_type,
            title=title,
            reference_number=reference_number,
            status=status,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_=metadata,
            created_by=created_by,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_reference(self, reference_number: str) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.reference_number == reference_number)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: str,
        *,
        pdf_url: str | None = None,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        if status not in {s.value for s in DocumentStatus}:
            raise ValueError(f"Invalid status: {status}")
        document.status = status
        if pdf_url is not None:
            document.pdf_url = pdf_url
        document.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return document

    async def bump_version(
        self,
        document_id: uuid.UUID,
        version_number: int,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        document.current_version = version_number
        document.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return document

    async def list_by_type(
        self,
        document_type: str,
        *,
        limit: int = 100,
    ) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.document_type == document_type)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(
                Document.entity_type == entity_type,
                Document.entity_id == entity_id,
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class DocumentVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        document_id: uuid.UUID,
        version_number: int,
        content: str,
        variables: dict | None = None,
        pdf_url: str | None = None,
        generated_by: int | None = None,
    ) -> DocumentVersion:
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            content=content,
            variables=variables,
            pdf_url=pdf_url,
            generated_by=generated_by,
        )
        self._session.add(version)
        await self._session.flush()
        return version

    async def get_by_id(self, version_id: uuid.UUID) -> DocumentVersion | None:
        result = await self._session.execute(
            select(DocumentVersion).where(DocumentVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_latest(self, document_id: uuid.UUID) -> DocumentVersion | None:
        result = await self._session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_document(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        result = await self._session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
        )
        return list(result.scalars().all())


class DocumentSignatureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        document_id: uuid.UUID,
        signer_name: str,
        signer_role: str,
        signed_at: datetime | None = None,
        version_id: uuid.UUID | None = None,
        signature_hash: str | None = None,
        signed_by_user_id: int | None = None,
        notes: str | None = None,
    ) -> DocumentSignature:
        if signer_role not in {r.value for r in SignerRole}:
            raise ValueError(f"Invalid signer_role: {signer_role}")

        signature = DocumentSignature(
            document_id=document_id,
            version_id=version_id,
            signer_name=signer_name,
            signer_role=signer_role,
            signed_at=signed_at or datetime.now(timezone.utc),
            signature_hash=signature_hash,
            signed_by_user_id=signed_by_user_id,
            notes=notes,
        )
        self._session.add(signature)
        await self._session.flush()
        return signature

    async def list_by_document(self, document_id: uuid.UUID) -> list[DocumentSignature]:
        result = await self._session.execute(
            select(DocumentSignature)
            .where(DocumentSignature.document_id == document_id)
            .order_by(DocumentSignature.signed_at.asc())
        )
        return list(result.scalars().all())
