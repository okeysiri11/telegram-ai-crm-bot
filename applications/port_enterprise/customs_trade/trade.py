"""International trade, compliance, and document management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

INCOTERMS = ["EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"]
DOC_TYPES = [
    "bl",
    "cmr",
    "rail_waybill",
    "air_waybill",
    "certificate_of_origin",
    "phytosanitary",
    "veterinary",
    "commercial_invoice",
    "packing_list",
    "other",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InternationalTrade:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_import(self, *, reference: str, origin_country: str, value: float = 0.0) -> dict[str, Any]:
        if not reference:
            raise ValidationError("import reference required")
        iid = _id("ct_imp")
        return self.store.ct_imports.save(
            iid,
            {
                "import_id": iid,
                "reference": reference,
                "origin_country": origin_country,
                "value": float(value),
                "status": "open",
                "created_at": _now(),
            },
        )

    def register_export(self, *, reference: str, destination_country: str, value: float = 0.0) -> dict[str, Any]:
        if not reference:
            raise ValidationError("export reference required")
        eid = _id("ct_exp")
        return self.store.ct_exports.save(
            eid,
            {
                "export_id": eid,
                "reference": reference,
                "destination_country": destination_country,
                "value": float(value),
                "status": "open",
                "created_at": _now(),
            },
        )

    def register_country(self, *, code: str, name: str) -> dict[str, Any]:
        if not code or not name:
            raise ValidationError("country code and name required")
        cid = _id("ct_cty")
        return self.store.ct_countries.save(
            cid, {"country_id": cid, "code": code.upper(), "name": name, "created_at": _now()}
        )

    def register_partner(self, *, name: str, country: str = "", role: str = "buyer") -> dict[str, Any]:
        if not name:
            raise ValidationError("partner name required")
        pid = _id("ct_prt")
        return self.store.ct_partners.save(
            pid,
            {
                "partner_id": pid,
                "name": name,
                "country": country,
                "role": role,
                "created_at": _now(),
            },
        )

    def trade_agreement(self, *, name: str, parties: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("agreement name required")
        aid = _id("ct_agr")
        return self.store.ct_agreements.save(
            aid,
            {
                "agreement_id": aid,
                "name": name,
                "parties": parties or [],
                "created_at": _now(),
            },
        )

    def set_incoterm(self, *, trade_ref: str, incoterm: str) -> dict[str, Any]:
        if incoterm not in INCOTERMS:
            raise ValidationError(f"incoterm must be one of {INCOTERMS}")
        iid = _id("ct_inc")
        return self.store.ct_incoterms.save(
            iid,
            {
                "incoterm_id": iid,
                "trade_ref": trade_ref,
                "incoterm": incoterm,
                "at": _now(),
            },
        )

    def letter_of_credit(self, *, reference: str, amount: float, bank: str = "") -> dict[str, Any]:
        if not reference:
            raise ValidationError("LC reference required")
        lid = _id("ct_lc")
        return self.store.ct_lcs.save(
            lid,
            {
                "lc_id": lid,
                "reference": reference,
                "amount": float(amount),
                "bank": bank,
                "status": "open",
                "created_at": _now(),
            },
        )

    def commercial_invoice(self, *, trade_ref: str, amount: float, currency: str = "USD") -> dict[str, Any]:
        iid = _id("ct_cinv")
        return self.store.ct_invoices.save(
            iid,
            {
                "invoice_id": iid,
                "trade_ref": trade_ref,
                "amount": float(amount),
                "currency": currency,
                "at": _now(),
            },
        )

    def packing_list(self, *, trade_ref: str, packages: int, weight_kg: float = 0.0) -> dict[str, Any]:
        pid = _id("ct_pkg")
        return self.store.ct_packing.save(
            pid,
            {
                "packing_id": pid,
                "trade_ref": trade_ref,
                "packages": int(packages),
                "weight_kg": float(weight_kg),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "imports": self.store.ct_imports.count(),
            "exports": self.store.ct_exports.count(),
            "partners": self.store.ct_partners.count(),
            "agreements": self.store.ct_agreements.count(),
        }


class ComplianceManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def screen_sanctions(self, *, party_name: str, country: str = "") -> dict[str, Any]:
        if not party_name:
            raise ValidationError("party_name required")
        hit = party_name.lower().startswith("sanctioned")
        sid = _id("ct_san")
        return self.store.ct_sanctions.save(
            sid,
            {
                "screening_id": sid,
                "party_name": party_name,
                "country": country,
                "hit": hit,
                "result": "blocked" if hit else "clear",
                "at": _now(),
            },
        )

    def register_restricted(self, *, hs_code: str, reason: str = "") -> dict[str, Any]:
        if not hs_code:
            raise ValidationError("hs_code required")
        rid = _id("ct_rst")
        return self.store.ct_restricted.save(
            rid, {"restricted_id": rid, "hs_code": hs_code, "reason": reason, "created_at": _now()}
        )

    def dual_use(self, *, item_ref: str, controlled: bool = True) -> dict[str, Any]:
        if not item_ref:
            raise ValidationError("item_ref required")
        did = _id("ct_dual")
        return self.store.ct_dual_use.save(
            did,
            {
                "control_id": did,
                "item_ref": item_ref,
                "controlled": bool(controlled),
                "at": _now(),
            },
        )

    def license(self, *, license_no: str, license_type: str = "import", expires_at: str = "") -> dict[str, Any]:
        if not license_no:
            raise ValidationError("license_no required")
        lid = _id("ct_lic")
        return self.store.ct_licenses.save(
            lid,
            {
                "license_id": lid,
                "license_no": license_no,
                "license_type": license_type,
                "expires_at": expires_at,
                "created_at": _now(),
            },
        )

    def certificate(self, *, cert_type: str, reference: str, issuer: str = "") -> dict[str, Any]:
        if not reference:
            raise ValidationError("certificate reference required")
        cid = _id("ct_cert")
        return self.store.ct_certificates.save(
            cid,
            {
                "certificate_id": cid,
                "cert_type": cert_type,
                "reference": reference,
                "issuer": issuer,
                "created_at": _now(),
            },
        )

    def audit(self, *, entity_type: str, entity_id: str, action: str) -> dict[str, Any]:
        aid = _id("ct_aud")
        return self.store.ct_audits.save(
            aid,
            {
                "audit_id": aid,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "at": _now(),
            },
        )

    def compliance_report(self, *, period: str = "monthly") -> dict[str, Any]:
        rid = _id("ct_crep")
        return self.store.ct_compliance_reports.save(
            rid,
            {
                "report_id": rid,
                "period": period,
                "screenings": self.store.ct_sanctions.count(),
                "restricted": self.store.ct_restricted.count(),
                "licenses": self.store.ct_licenses.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "sanctions_screenings": self.store.ct_sanctions.count(),
            "restricted": self.store.ct_restricted.count(),
            "licenses": self.store.ct_licenses.count(),
            "audits": self.store.ct_audits.count(),
        }


class DocumentManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def store_document(
        self,
        *,
        doc_type: str,
        title: str,
        reference: str = "",
        trade_ref: str = "",
    ) -> dict[str, Any]:
        if doc_type not in DOC_TYPES:
            raise ValidationError(f"doc_type must be one of {DOC_TYPES}")
        if not title:
            raise ValidationError("document title required")
        did = _id("ct_doc")
        return self.store.ct_documents.save(
            did,
            {
                "document_id": did,
                "doc_type": doc_type,
                "title": title,
                "reference": reference,
                "trade_ref": trade_ref,
                "signed": False,
                "created_at": _now(),
            },
        )

    def sign(self, document_id: str, *, signer: str) -> dict[str, Any]:
        doc = self.store.ct_documents.get(document_id)
        if doc is None:
            raise NotFoundError("document", document_id)
        if not signer:
            raise ValidationError("signer required")
        doc["signed"] = True
        doc["signer"] = signer
        doc["signed_at"] = _now()
        self.store.ct_documents.save(document_id, doc)
        sid = _id("ct_sig")
        return self.store.ct_signatures.save(
            sid,
            {
                "signature_id": sid,
                "document_id": document_id,
                "signer": signer,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "documents": self.store.ct_documents.count(),
            "signatures": self.store.ct_signatures.count(),
            "doc_types": list(DOC_TYPES),
        }
