"""Document management — filings, evidence, versions, signatures."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DOC_TYPES = ("legal", "evidence", "filing")


class DocumentManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store

    def register_document(
        self,
        *,
        case_id: str,
        title: str,
        document_type: str = "legal",
        uri: str = "",
        version: str = "1.0",
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title:
            raise ValidationError("title required")
        dt = document_type.lower().strip()
        if dt not in DOC_TYPES:
            raise ValidationError(f"document_type must be one of {list(DOC_TYPES)}")
        did = _id("cm_doc")
        record = {
            "document_id": did,
            "case_id": case_id,
            "title": title,
            "document_type": dt,
            "uri": uri or f"vault://cases/{case_id}/{did}",
            "version": version,
            "signed": False,
            "created_at": _now(),
        }
        self.store.cm_documents.save(did, record)
        self.record_version(document_id=did, version=version, summary="initial")
        return record

    def register_evidence(self, *, case_id: str, title: str, uri: str = "") -> dict[str, Any]:
        return self.register_document(case_id=case_id, title=title, document_type="evidence", uri=uri)

    def register_filing(self, *, case_id: str, title: str, uri: str = "") -> dict[str, Any]:
        return self.register_document(case_id=case_id, title=title, document_type="filing", uri=uri)

    def record_version(
        self, *, document_id: str, version: str, summary: str = ""
    ) -> dict[str, Any]:
        doc = self.store.cm_documents.get(document_id)
        if doc is None:
            raise NotFoundError("document", document_id)
        if not version:
            raise ValidationError("version required")
        doc["version"] = version
        self.store.cm_documents.save(document_id, doc)
        vid = _id("cm_dver")
        return self.store.cm_doc_versions.save(
            vid,
            {
                "version_id": vid,
                "document_id": document_id,
                "version": version,
                "summary": summary,
                "at": _now(),
            },
        )

    def secure_store(self, *, document_id: str, vault_ref: str) -> dict[str, Any]:
        doc = self.store.cm_documents.get(document_id)
        if doc is None:
            raise NotFoundError("document", document_id)
        if not vault_ref:
            raise ValidationError("vault_ref required")
        doc["uri"] = vault_ref
        self.store.cm_documents.save(document_id, doc)
        sid = _id("cm_sec")
        return self.store.cm_secure_storage.save(
            sid,
            {
                "storage_id": sid,
                "document_id": document_id,
                "vault_ref": vault_ref,
                "at": _now(),
            },
        )

    def digital_signature(
        self, *, document_id: str, signer: str, signature_ref: str = ""
    ) -> dict[str, Any]:
        doc = self.store.cm_documents.get(document_id)
        if doc is None:
            raise NotFoundError("document", document_id)
        if not signer:
            raise ValidationError("signer required")
        doc["signed"] = True
        self.store.cm_documents.save(document_id, doc)
        sid = _id("cm_sig")
        return self.store.cm_signatures.save(
            sid,
            {
                "signature_id": sid,
                "document_id": document_id,
                "signer": signer,
                "signature_ref": signature_ref or f"sig://{document_id}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "documents": self.store.cm_documents.count(),
            "versions": self.store.cm_doc_versions.count(),
            "secure_storage": self.store.cm_secure_storage.count(),
            "signatures": self.store.cm_signatures.count(),
        }
