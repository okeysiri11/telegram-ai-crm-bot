# Compliance Engine — document completeness and trade compliance checks.

from __future__ import annotations

import time

from applications.port_erp.certificates.engine import CertificateManager, certificate_manager
from applications.port_erp.customs.models import (
    ComplianceCheck,
    ComplianceStatus,
    DocumentType,
)
from applications.port_erp.documents.engine import CargoDocumentationEngine, cargo_documentation_engine
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


_REQUIRED_EXPORT = {
    DocumentType.COMMERCIAL_INVOICE,
    DocumentType.PACKING_LIST,
    DocumentType.EXPORT_DECLARATION,
    DocumentType.BILL_OF_LADING,
}

_REQUIRED_IMPORT = {
    DocumentType.COMMERCIAL_INVOICE,
    DocumentType.PACKING_LIST,
    DocumentType.IMPORT_DECLARATION,
    DocumentType.BILL_OF_LADING,
}


class ComplianceEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        documents: CargoDocumentationEngine | None = None,
        certificates: CertificateManager | None = None,
    ) -> None:
        self._store = store or port_store
        self._documents = documents or cargo_documentation_engine
        self._certificates = certificates or certificate_manager

    def create_check(self, check: ComplianceCheck) -> ComplianceCheck:
        if not check.shipment_id and not check.cargo_id:
            raise ValidationError("shipment_id or cargo_id is required")
        return self._store.compliance_checks.save(check.check_id, check)

    def get(self, check_id: str) -> ComplianceCheck:
        check = self._store.compliance_checks.get(check_id)
        if check is None:
            raise NotFoundError("ComplianceCheck", check_id)
        return check

    def list_checks(self, *, shipment_id: str | None = None) -> list[ComplianceCheck]:
        items = self._store.compliance_checks.list_all()
        if shipment_id:
            items = [c for c in items if c.shipment_id == shipment_id]
        return items

    def evaluate_documents(
        self,
        *,
        shipment_id: str,
        cargo_id: str = "",
        direction: str = "export",
    ) -> ComplianceCheck:
        required = _REQUIRED_EXPORT if direction == "export" else _REQUIRED_IMPORT
        docs = self._documents.list_documents(shipment_id=shipment_id, cargo_id=cargo_id or None)
        present = {d.document_type for d in docs}
        missing = [t.value for t in required if t not in present]
        status = ComplianceStatus.COMPLIANT if not missing else ComplianceStatus.NON_COMPLIANT
        findings = [f"missing:{m}" for m in missing]
        certs = self._certificates.list_certificates(shipment_id=shipment_id)
        if not certs:
            findings.append("no_certificates")
            if status == ComplianceStatus.COMPLIANT:
                status = ComplianceStatus.UNDER_REVIEW
        check = ComplianceCheck(
            shipment_id=shipment_id,
            cargo_id=cargo_id,
            check_type="document_completeness",
            status=status,
            findings=findings,
            completed_at=time.time(),
        )
        return self._store.compliance_checks.save(check.check_id, check)


compliance_engine = ComplianceEngine()
