# Document Engine v1 — document generation, versioning, signatures, PDF export.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import OWNER_ID
from database.models.document_engine import DocumentStatus, DocumentType, SignerRole
from database.session import get_session
from repositories.document_engine_repository import (
    DocumentRepository,
    DocumentSignatureRepository,
    DocumentTemplateRepository,
    DocumentVersionRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.document_pdf_exporter import (
    content_to_pdf_bytes,
    export_pdf_to_file,
    render_template,
    signature_hash,
)

DOCUMENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT", "LAWYER"})
PDF_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "storage" / "documents"

DEFAULT_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "code": "INVOICE_STANDARD",
        "name": "Standard Invoice",
        "document_type": DocumentType.INVOICE.value,
        "content_template": (
            "# Invoice\n\n"
            "Invoice No: {{invoice_number}}\n"
            "Date: {{invoice_date}}\n\n"
            "Bill To: {{buyer_name}}\n"
            "Seller: {{seller_name}}\n\n"
            "Vehicle: {{vehicle_description}}\n"
            "VIN: {{vin}}\n\n"
            "Amount: {{amount}} {{currency}}\n"
            "Payment Terms: {{payment_terms}}\n"
        ),
        "default_variables": {
            "currency": "USD",
            "payment_terms": "Net 30",
        },
    },
    {
        "code": "PURCHASE_CONTRACT_STANDARD",
        "name": "Purchase Contract",
        "document_type": DocumentType.PURCHASE_CONTRACT.value,
        "content_template": (
            "# Purchase Contract\n\n"
            "Contract No: {{contract_number}}\n"
            "Date: {{contract_date}}\n\n"
            "Buyer: {{buyer_name}}\n"
            "Seller: {{seller_name}}\n\n"
            "Vehicle: {{vehicle_description}}\n"
            "VIN: {{vin}}\n"
            "Purchase Price: {{amount}} {{currency}}\n\n"
            "Terms: {{terms}}\n"
        ),
        "default_variables": {"currency": "USD"},
    },
    {
        "code": "SALES_CONTRACT_STANDARD",
        "name": "Sales Contract",
        "document_type": DocumentType.SALES_CONTRACT.value,
        "content_template": (
            "# Sales Contract\n\n"
            "Contract No: {{contract_number}}\n"
            "Date: {{contract_date}}\n\n"
            "Seller: {{seller_name}}\n"
            "Buyer: {{buyer_name}}\n\n"
            "Vehicle: {{vehicle_description}}\n"
            "VIN: {{vin}}\n"
            "Sale Price: {{amount}} {{currency}}\n\n"
            "Delivery Date: {{delivery_date}}\n"
            "Terms: {{terms}}\n"
        ),
        "default_variables": {"currency": "USD"},
    },
    {
        "code": "CUSTOMS_DECLARATION",
        "name": "Customs Declaration",
        "document_type": DocumentType.CUSTOMS_DOCUMENT.value,
        "content_template": (
            "# Customs Declaration\n\n"
            "Declaration No: {{declaration_number}}\n"
            "Date: {{declaration_date}}\n\n"
            "Importer: {{importer_name}}\n"
            "Origin Country: {{origin_country}}\n"
            "Destination Port: {{destination_port}}\n\n"
            "Vehicle: {{vehicle_description}}\n"
            "VIN: {{vin}}\n"
            "HS Code: {{hs_code}}\n"
            "Declared Value: {{amount}} {{currency}}\n"
        ),
        "default_variables": {"currency": "USD"},
    },
    {
        "code": "DELIVERY_ACT_STANDARD",
        "name": "Delivery Act",
        "document_type": DocumentType.DELIVERY_ACT.value,
        "content_template": (
            "# Delivery Act\n\n"
            "Act No: {{act_number}}\n"
            "Date: {{delivery_date}}\n\n"
            "Delivered To: {{recipient_name}}\n"
            "Delivered By: {{deliverer_name}}\n\n"
            "Vehicle: {{vehicle_description}}\n"
            "VIN: {{vin}}\n"
            "Mileage: {{mileage}}\n"
            "Condition Notes: {{condition_notes}}\n"
        ),
        "default_variables": {},
    },
)


class DocumentEngineError(Exception):
    pass


class DocumentEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in DOCUMENT_ROLES for role in roles)

    @staticmethod
    def _template_snapshot(template) -> dict[str, Any]:
        return {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "document_type": template.document_type,
            "is_active": template.is_active,
            "description": template.description,
            "default_variables": template.default_variables,
        }

    @staticmethod
    def _document_snapshot(document) -> dict[str, Any]:
        return {
            "id": str(document.id),
            "template_id": str(document.template_id) if document.template_id else None,
            "document_type": document.document_type,
            "title": document.title,
            "reference_number": document.reference_number,
            "status": document.status,
            "entity_type": document.entity_type,
            "entity_id": str(document.entity_id) if document.entity_id else None,
            "current_version": document.current_version,
            "metadata": document.metadata_,
            "pdf_url": document.pdf_url,
            "created_by": document.created_by,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }

    @staticmethod
    def _version_snapshot(version) -> dict[str, Any]:
        return {
            "id": str(version.id),
            "document_id": str(version.document_id),
            "version_number": version.version_number,
            "content": version.content,
            "variables": version.variables,
            "pdf_url": version.pdf_url,
            "generated_by": version.generated_by,
            "created_at": version.created_at.isoformat(),
        }

    @staticmethod
    def _signature_snapshot(signature) -> dict[str, Any]:
        return {
            "id": str(signature.id),
            "document_id": str(signature.document_id),
            "version_id": str(signature.version_id) if signature.version_id else None,
            "signer_name": signature.signer_name,
            "signer_role": signature.signer_role,
            "signed_at": signature.signed_at.isoformat(),
            "signature_hash": signature.signature_hash,
            "signed_by_user_id": signature.signed_by_user_id,
            "notes": signature.notes,
        }

    @staticmethod
    def _merge_variables(
        template_defaults: dict | None,
        overrides: dict[str, str] | None,
    ) -> dict[str, str]:
        merged: dict[str, str] = {}
        if template_defaults:
            merged.update({k: str(v) for k, v in template_defaults.items()})
        if overrides:
            merged.update({k: str(v) for k, v in overrides.items()})
        return merged

    @staticmethod
    def _reference_number(document_type: str) -> str:
        prefix = document_type[:3]
        suffix = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{suffix}"

    @staticmethod
    async def bootstrap_default_templates(actor_id: int) -> list[dict[str, Any]]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        created: list[dict[str, Any]] = []
        async with get_session() as session:
            repo = DocumentTemplateRepository(session)
            for spec in DEFAULT_TEMPLATES:
                existing = await repo.get_by_code(spec["code"])
                if existing is not None:
                    continue
                template = await repo.create(**spec)
                created.append(DocumentEngineV1._template_snapshot(template))
        return created

    @staticmethod
    async def create_template(
        actor_id: int,
        *,
        code: str,
        name: str,
        document_type: str,
        content_template: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            repo = DocumentTemplateRepository(session)
            if await repo.get_by_code(code):
                raise DocumentEngineError(f"Template already exists: {code}")
            template = await repo.create(
                code=code,
                name=name,
                document_type=document_type,
                content_template=content_template,
                **fields,
            )
            return DocumentEngineV1._template_snapshot(template)

    @staticmethod
    async def list_templates(
        actor_id: int,
        *,
        document_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            repo = DocumentTemplateRepository(session)
            if document_type:
                templates = await repo.list_by_type(document_type)
            else:
                templates = await repo.list_all()
            return [DocumentEngineV1._template_snapshot(t) for t in templates]

    @staticmethod
    async def generate_document(
        actor_id: int,
        *,
        template_code: str,
        title: str,
        variables: dict[str, str] | None = None,
        reference_number: str | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            template_repo = DocumentTemplateRepository(session)
            template = await template_repo.get_by_code(template_code)
            if template is None:
                raise DocumentEngineError(f"Template not found: {template_code}")

            merged = DocumentEngineV1._merge_variables(
                template.default_variables,
                variables,
            )
            content = render_template(template.content_template, merged)
            ref = reference_number or DocumentEngineV1._reference_number(
                template.document_type
            )

            doc_repo = DocumentRepository(session)
            if await doc_repo.get_by_reference(ref):
                raise DocumentEngineError(f"Reference number already exists: {ref}")

            document = await doc_repo.create(
                template_id=template.id,
                document_type=template.document_type,
                title=title,
                reference_number=ref,
                status=DocumentStatus.GENERATED.value,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=metadata,
                created_by=actor_id,
            )
            version = await DocumentVersionRepository(session).create(
                document_id=document.id,
                version_number=1,
                content=content,
                variables=merged,
                generated_by=actor_id,
            )
            await doc_repo.bump_version(document.id, 1)

            return {
                "document": DocumentEngineV1._document_snapshot(document),
                "version": DocumentEngineV1._version_snapshot(version),
            }

    @staticmethod
    async def generate_invoice(
        actor_id: int,
        *,
        buyer_name: str,
        seller_name: str,
        vehicle_description: str,
        vin: str,
        amount: str,
        **fields: Any,
    ) -> dict[str, Any]:
        variables = {
            "invoice_number": fields.pop("invoice_number", DocumentEngineV1._reference_number("INV")),
            "invoice_date": fields.pop(
                "invoice_date",
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
            "buyer_name": buyer_name,
            "seller_name": seller_name,
            "vehicle_description": vehicle_description,
            "vin": vin,
            "amount": amount,
            "currency": fields.pop("currency", "USD"),
            "payment_terms": fields.pop("payment_terms", "Net 30"),
        }
        return await DocumentEngineV1.generate_document(
            actor_id,
            template_code="INVOICE_STANDARD",
            title=f"Invoice — {vin}",
            variables=variables,
            reference_number=variables["invoice_number"],
            **fields,
        )

    @staticmethod
    async def generate_purchase_contract(
        actor_id: int,
        *,
        buyer_name: str,
        seller_name: str,
        vehicle_description: str,
        vin: str,
        amount: str,
        **fields: Any,
    ) -> dict[str, Any]:
        variables = {
            "contract_number": fields.pop(
                "contract_number",
                DocumentEngineV1._reference_number("PUR"),
            ),
            "contract_date": fields.pop(
                "contract_date",
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
            "buyer_name": buyer_name,
            "seller_name": seller_name,
            "vehicle_description": vehicle_description,
            "vin": vin,
            "amount": amount,
            "currency": fields.pop("currency", "USD"),
            "terms": fields.pop("terms", "Standard purchase terms apply."),
        }
        return await DocumentEngineV1.generate_document(
            actor_id,
            template_code="PURCHASE_CONTRACT_STANDARD",
            title=f"Purchase Contract — {vin}",
            variables=variables,
            reference_number=variables["contract_number"],
            **fields,
        )

    @staticmethod
    async def generate_sales_contract(
        actor_id: int,
        *,
        buyer_name: str,
        seller_name: str,
        vehicle_description: str,
        vin: str,
        amount: str,
        **fields: Any,
    ) -> dict[str, Any]:
        variables = {
            "contract_number": fields.pop(
                "contract_number",
                DocumentEngineV1._reference_number("SAL"),
            ),
            "contract_date": fields.pop(
                "contract_date",
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
            "buyer_name": buyer_name,
            "seller_name": seller_name,
            "vehicle_description": vehicle_description,
            "vin": vin,
            "amount": amount,
            "currency": fields.pop("currency", "USD"),
            "delivery_date": fields.pop("delivery_date", ""),
            "terms": fields.pop("terms", "Standard sales terms apply."),
        }
        return await DocumentEngineV1.generate_document(
            actor_id,
            template_code="SALES_CONTRACT_STANDARD",
            title=f"Sales Contract — {vin}",
            variables=variables,
            reference_number=variables["contract_number"],
            **fields,
        )

    @staticmethod
    async def generate_customs_document(
        actor_id: int,
        *,
        importer_name: str,
        vehicle_description: str,
        vin: str,
        amount: str,
        **fields: Any,
    ) -> dict[str, Any]:
        variables = {
            "declaration_number": fields.pop(
                "declaration_number",
                DocumentEngineV1._reference_number("CUS"),
            ),
            "declaration_date": fields.pop(
                "declaration_date",
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
            "importer_name": importer_name,
            "origin_country": fields.pop("origin_country", ""),
            "destination_port": fields.pop("destination_port", ""),
            "vehicle_description": vehicle_description,
            "vin": vin,
            "hs_code": fields.pop("hs_code", "8703"),
            "amount": amount,
            "currency": fields.pop("currency", "USD"),
        }
        return await DocumentEngineV1.generate_document(
            actor_id,
            template_code="CUSTOMS_DECLARATION",
            title=f"Customs Declaration — {vin}",
            variables=variables,
            reference_number=variables["declaration_number"],
            **fields,
        )

    @staticmethod
    async def generate_delivery_act(
        actor_id: int,
        *,
        recipient_name: str,
        deliverer_name: str,
        vehicle_description: str,
        vin: str,
        **fields: Any,
    ) -> dict[str, Any]:
        variables = {
            "act_number": fields.pop(
                "act_number",
                DocumentEngineV1._reference_number("DEL"),
            ),
            "delivery_date": fields.pop(
                "delivery_date",
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ),
            "recipient_name": recipient_name,
            "deliverer_name": deliverer_name,
            "vehicle_description": vehicle_description,
            "vin": vin,
            "mileage": fields.pop("mileage", ""),
            "condition_notes": fields.pop("condition_notes", "Vehicle received in good condition."),
        }
        return await DocumentEngineV1.generate_document(
            actor_id,
            template_code="DELIVERY_ACT_STANDARD",
            title=f"Delivery Act — {vin}",
            variables=variables,
            reference_number=variables["act_number"],
            **fields,
        )

    @staticmethod
    async def create_new_version(
        actor_id: int,
        document_id: uuid.UUID,
        *,
        content: str | None = None,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(document_id)
            if document is None:
                raise DocumentEngineError(f"Document not found: {document_id}")

            version_repo = DocumentVersionRepository(session)
            latest = await version_repo.get_latest(document_id)
            next_version = (latest.version_number if latest else 0) + 1

            if content is None:
                if variables is None:
                    raise DocumentEngineError(
                        "content or variables required for new version"
                    )
                template = None
                if document.template_id:
                    template = await DocumentTemplateRepository(session).get_by_id(
                        document.template_id
                    )
                if template is None:
                    raise DocumentEngineError("Cannot re-render without template")
                merged = DocumentEngineV1._merge_variables(
                    template.default_variables,
                    variables,
                )
                content = render_template(template.content_template, merged)
            else:
                merged = variables

            version = await version_repo.create(
                document_id=document_id,
                version_number=next_version,
                content=content,
                variables=merged,
                generated_by=actor_id,
            )
            await doc_repo.bump_version(document_id, next_version)
            await doc_repo.update_status(document_id, DocumentStatus.GENERATED.value)

            return DocumentEngineV1._version_snapshot(version)

    @staticmethod
    async def add_signature(
        actor_id: int,
        document_id: uuid.UUID,
        *,
        signer_name: str,
        signer_role: str,
        version_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(document_id)
            if document is None:
                raise DocumentEngineError(f"Document not found: {document_id}")

            version_repo = DocumentVersionRepository(session)
            version = (
                await version_repo.get_by_id(version_id)
                if version_id
                else await version_repo.get_latest(document_id)
            )
            if version is None:
                raise DocumentEngineError("No document version to sign")

            signed_at = datetime.now(timezone.utc)
            sig_hash = signature_hash(
                version.content,
                signer_name,
                signed_at.isoformat(),
            )
            signature = await DocumentSignatureRepository(session).create(
                document_id=document_id,
                version_id=version.id,
                signer_name=signer_name,
                signer_role=signer_role,
                signed_at=signed_at,
                signature_hash=sig_hash,
                signed_by_user_id=actor_id,
                notes=notes,
            )
            await doc_repo.update_status(document_id, DocumentStatus.SIGNED.value)

            return DocumentEngineV1._signature_snapshot(signature)

    @staticmethod
    async def export_pdf(
        actor_id: int,
        document_id: uuid.UUID,
        *,
        version_number: int | None = None,
        save_to_disk: bool = True,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(document_id)
            if document is None:
                raise DocumentEngineError(f"Document not found: {document_id}")

            version_repo = DocumentVersionRepository(session)
            if version_number is not None:
                versions = await version_repo.list_by_document(document_id)
                version = next(
                    (v for v in versions if v.version_number == version_number),
                    None,
                )
            else:
                version = await version_repo.get_latest(document_id)

            if version is None:
                raise DocumentEngineError("No document version to export")

            pdf_path: str | None = None
            pdf_bytes = content_to_pdf_bytes(
                title=document.title,
                content=version.content,
                reference_number=document.reference_number,
            )

            if save_to_disk:
                pdf_path, _ = export_pdf_to_file(
                    output_dir=PDF_OUTPUT_DIR,
                    reference_number=document.reference_number,
                    title=document.title,
                    content=version.content,
                )
                version.pdf_url = pdf_path
                document.pdf_url = pdf_path
                document.updated_at = datetime.now(timezone.utc)
                await session.flush()

            return {
                "document_id": str(document_id),
                "version_number": version.version_number,
                "pdf_url": pdf_path,
                "pdf_size_bytes": len(pdf_bytes),
                "pdf_bytes_available": True,
            }

    @staticmethod
    async def get_document(
        actor_id: int,
        document_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is None:
                raise DocumentEngineError(f"Document not found: {document_id}")

            versions = await DocumentVersionRepository(session).list_by_document(
                document_id
            )
            signatures = await DocumentSignatureRepository(session).list_by_document(
                document_id
            )
            return {
                "document": DocumentEngineV1._document_snapshot(document),
                "versions": [DocumentEngineV1._version_snapshot(v) for v in versions],
                "signatures": [
                    DocumentEngineV1._signature_snapshot(s) for s in signatures
                ],
            }

    @staticmethod
    async def list_documents(
        actor_id: int,
        *,
        document_type: str | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await DocumentEngineV1.user_can_access(actor_id):
            raise DocumentEngineError("Access denied")

        async with get_session() as session:
            repo = DocumentRepository(session)
            if entity_type and entity_id:
                documents = await repo.list_by_entity(entity_type, entity_id, limit=limit)
            elif document_type:
                documents = await repo.list_by_type(document_type, limit=limit)
            else:
                documents = []
                for doc_type in DocumentType:
                    documents.extend(
                        await repo.list_by_type(doc_type.value, limit=limit)
                    )
                documents.sort(key=lambda d: d.created_at, reverse=True)
                documents = documents[:limit]

            return [DocumentEngineV1._document_snapshot(d) for d in documents]
