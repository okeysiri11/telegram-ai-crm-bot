# Document Engine — templates, PDF, signatures, version history.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.auto_marketplace.finance.ai_assistant import FinanceAIAssistant, finance_ai_assistant
from applications.auto_marketplace.finance.events import DocumentCreatedEvent
from applications.auto_marketplace.finance.models import Document, DocumentStatus, DocumentTemplate, DocumentVersion
from applications.auto_marketplace.finance.security import FinanceSecurity, finance_security
from applications.auto_marketplace.finance.workflow_bridge import FinanceWorkflowBridge, finance_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DocumentEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: FinanceAIAssistant | None = None,
        security: FinanceSecurity | None = None,
        workflow: FinanceWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or finance_ai_assistant
        self._security = security or finance_security
        self._workflow = workflow or finance_workflow_bridge

    def _ensure_templates(self) -> None:
        if self._store.document_templates.count() == 0:
            self._seed_templates()

    def _seed_templates(self) -> None:
        defaults = [
            DocumentTemplate(name="Purchase Agreement", category="contract", content="Purchase agreement for {{vehicle}} at {{amount}} {{currency}}.", variables=["vehicle", "amount", "currency"]),
            DocumentTemplate(name="Invoice", category="invoice", content="Invoice #{{invoice_id}} — Total: {{total}} {{currency}}.", variables=["invoice_id", "total", "currency"]),
        ]
        for tpl in defaults:
            self._store.document_templates.save(tpl.template_id, tpl)

    def create_template(self, template: DocumentTemplate) -> DocumentTemplate:
        return self._store.document_templates.save(template.template_id, template)

    def get_template(self, template_id: str) -> DocumentTemplate:
        tpl = self._store.document_templates.get(template_id)
        if tpl is None:
            raise NotFoundError("DocumentTemplate", template_id)
        return tpl

    def list_templates(self, *, category: str = "") -> list[DocumentTemplate]:
        self._ensure_templates()
        items = self._store.document_templates.list_all()
        if category:
            return [t for t in items if t.category == category]
        return items

    async def generate_from_template(
        self,
        template_id: str,
        *,
        title: str,
        variables: dict[str, Any],
        customer_id: str = "",
        deal_id: str = "",
        actor_id: str = "system",
    ) -> Document:
        template = self.get_template(template_id)
        content = await self._ai.generate_document_content(template.content, variables)
        doc = Document(
            title=title or template.name,
            category=template.category,
            template_id=template_id,
            customer_id=customer_id,
            deal_id=deal_id,
            content=content,
            versions=[DocumentVersion(version=1, content=content, created_by=actor_id)],
        )
        doc.pdf_url = f"/documents/{doc.document_id}.pdf"
        category = await self._ai.classify_document(doc)
        doc.category = category
        self._store.finance_documents.save(doc.document_id, doc)
        self._security.audit(actor_id=actor_id, action="create", resource_type="document", resource_id=doc.document_id)
        await publish(DocumentCreatedEvent(document_id=doc.document_id, category=doc.category, customer_id=customer_id))
        return doc

    def get(self, document_id: str) -> Document:
        doc = self._store.finance_documents.get(document_id)
        if doc is None:
            raise NotFoundError("Document", document_id)
        return doc

    def list_documents(self, *, customer_id: str = "", category: str = "") -> list[Document]:
        items = self._store.finance_documents.list_all()
        if customer_id:
            items = [d for d in items if d.customer_id == customer_id]
        if category:
            items = [d for d in items if d.category == category]
        return items

    def update(self, document_id: str, content: str, *, actor_id: str = "system") -> Document:
        doc = self.get(document_id)
        version = len(doc.versions) + 1
        doc.versions.append(DocumentVersion(version=version, content=content, created_by=actor_id))
        doc.content = content
        doc.updated_at = time.time()
        self._store.finance_documents.save(document_id, doc)
        self._security.audit(actor_id=actor_id, action="update", resource_type="document", resource_id=document_id)
        return doc

    async def submit_for_approval(self, document_id: str, *, approver_id: str) -> Document:
        doc = self.get(document_id)
        doc.status = DocumentStatus.PENDING_APPROVAL
        workflow_id = await self._workflow.document_approval(document_id, approver_id)
        doc.metadata["approval_workflow_id"] = workflow_id
        self._store.finance_documents.save(document_id, doc)
        return doc

    def approve(self, document_id: str, *, actor_id: str = "system") -> Document:
        doc = self.get(document_id)
        doc.status = DocumentStatus.APPROVED
        self._store.finance_documents.save(document_id, doc)
        self._security.audit(actor_id=actor_id, action="approve", resource_type="document", resource_id=document_id)
        return doc

    def sign(self, document_id: str, *, signed_by: str, signature_id: str = "") -> Document:
        doc = self.get(document_id)
        doc.status = DocumentStatus.SIGNED
        doc.signature_id = signature_id or f"sig-{document_id[:8]}"
        doc.metadata["signed_by"] = signed_by
        self._store.finance_documents.save(document_id, doc)
        self._security.audit(actor_id=signed_by, action="sign", resource_type="document", resource_id=document_id)
        return doc

    def export_document(self, document_id: str) -> dict[str, Any]:
        doc = self.get(document_id)
        return {"document_id": doc.document_id, "pdf_url": doc.pdf_url, "content": doc.content, "format": "pdf"}

    def import_document(self, payload: dict[str, Any], *, actor_id: str = "system") -> Document:
        doc = Document(
            title=payload.get("title", "Imported Document"),
            category=payload.get("category", "imported"),
            content=payload.get("content", ""),
            customer_id=payload.get("customer_id", ""),
            deal_id=payload.get("deal_id", ""),
        )
        self._store.finance_documents.save(doc.document_id, doc)
        self._security.audit(actor_id=actor_id, action="import", resource_type="document", resource_id=doc.document_id)
        return doc


document_engine = DocumentEngine()
