"""Document ingest — PDF/DOCX/OCR, parsing, classification."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DocumentIngest:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.formats = list(DEFAULT_CONFIG.di_formats)
        self.doc_classes = list(DEFAULT_CONFIG.di_doc_classes)

    def import_document(
        self,
        *,
        title: str,
        format: str = "pdf",
        uri: str = "",
        content: str = "",
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        fmt = format.lower().strip()
        if fmt not in self.formats:
            raise ValidationError(f"format must be one of {self.formats}")
        did = _id("di_doc")
        return self.store.di_documents.save(
            did,
            {
                "document_id": did,
                "title": title,
                "format": fmt,
                "uri": uri or f"vault://di/{did}",
                "content": content,
                "status": "imported",
                "created_at": _now(),
            },
        )

    def process_pdf(self, *, document_id: str = "", title: str = "", content: str = "") -> dict[str, Any]:
        doc = self._ensure(document_id=document_id, title=title or "PDF Document", format="pdf", content=content)
        return self._process(doc, engine="pdf")

    def process_docx(self, *, document_id: str = "", title: str = "", content: str = "") -> dict[str, Any]:
        doc = self._ensure(document_id=document_id, title=title or "DOCX Document", format="docx", content=content)
        return self._process(doc, engine="docx")

    def run_ocr(self, *, document_id: str, engine: str = "tesseract") -> dict[str, Any]:
        doc = self.store.di_documents.get(document_id)
        if doc is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("document", document_id)
        oid = _id("di_ocr")
        text = doc.get("content") or f"OCR text extracted via {engine}"
        return self.store.di_ocr.save(
            oid,
            {
                "ocr_id": oid,
                "document_id": document_id,
                "engine": engine,
                "text": text,
                "confidence": 0.92,
                "at": _now(),
            },
        )

    def parse(self, *, document_id: str) -> dict[str, Any]:
        doc = self.store.di_documents.get(document_id)
        if doc is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("document", document_id)
        pid = _id("di_parse")
        return self.store.di_parses.save(
            pid,
            {
                "parse_id": pid,
                "document_id": document_id,
                "sections": ["preamble", "definitions", "obligations", "signatures"],
                "word_count": max(1, len((doc.get("content") or "").split())),
                "at": _now(),
            },
        )

    def extract_metadata(self, *, document_id: str) -> dict[str, Any]:
        doc = self.store.di_documents.get(document_id)
        if doc is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("document", document_id)
        mid = _id("di_meta")
        return self.store.di_metadata.save(
            mid,
            {
                "metadata_id": mid,
                "document_id": document_id,
                "title": doc.get("title"),
                "format": doc.get("format"),
                "uri": doc.get("uri"),
                "extracted_at": _now(),
            },
        )

    def classify(self, *, document_id: str, label: str, confidence: float = 0.85) -> dict[str, Any]:
        if self.store.di_documents.get(document_id) is None:
            from applications.legal_enterprise.shared.exceptions import NotFoundError

            raise NotFoundError("document", document_id)
        lab = label.lower().strip()
        if lab not in self.doc_classes:
            raise ValidationError(f"label must be one of {self.doc_classes}")
        cid = _id("di_dcls")
        return self.store.di_classifications.save(
            cid,
            {
                "classification_id": cid,
                "document_id": document_id,
                "label": lab,
                "confidence": max(0.0, min(1.0, float(confidence))),
                "at": _now(),
            },
        )

    def _ensure(
        self, *, document_id: str, title: str, format: str, content: str
    ) -> dict[str, Any]:
        if document_id:
            doc = self.store.di_documents.get(document_id)
            if doc is None:
                from applications.legal_enterprise.shared.exceptions import NotFoundError

                raise NotFoundError("document", document_id)
            return doc
        return self.import_document(title=title, format=format, content=content)

    def _process(self, doc: dict[str, Any], *, engine: str) -> dict[str, Any]:
        pid = _id("di_proc")
        return self.store.di_processing.save(
            pid,
            {
                "processing_id": pid,
                "document_id": doc["document_id"],
                "engine": engine,
                "status": "processed",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "documents": self.store.di_documents.count(),
            "processing": self.store.di_processing.count(),
            "ocr": self.store.di_ocr.count(),
            "parses": self.store.di_parses.count(),
            "metadata": self.store.di_metadata.count(),
            "classifications": self.store.di_classifications.count(),
        }
