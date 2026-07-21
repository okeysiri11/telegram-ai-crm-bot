# CertificationService — quality certificates verification.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.product_catalog.events import QualityVerifiedEvent
from applications.agro_marketplace.product_catalog.models import QualityCertificateRecord, QualityGrade
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CertificationService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def issue(self, certificate: QualityCertificateRecord) -> QualityCertificateRecord:
        return self._store.quality_certificates.save(certificate.certificate_id, certificate)

    def get(self, certificate_id: str) -> QualityCertificateRecord:
        cert = self._store.quality_certificates.get(certificate_id)
        if cert is None:
            raise NotFoundError("QualityCertificate", certificate_id)
        return cert

    def list_certificates(self, *, harvest_id: str | None = None) -> list[QualityCertificateRecord]:
        items = self._store.quality_certificates.list_all()
        if harvest_id:
            items = [c for c in items if c.harvest_id == harvest_id]
        return items

    async def verify(self, certificate_id: str, *, grade: QualityGrade | str | None = None) -> QualityCertificateRecord:
        cert = self.get(certificate_id)
        cert.verified = True
        if grade is not None:
            cert.grade = QualityGrade(grade) if isinstance(grade, str) else grade
        saved = self._store.quality_certificates.save(certificate_id, cert)
        await publish(
            QualityVerifiedEvent(
                certificate_id=saved.certificate_id,
                harvest_id=saved.harvest_id,
                grade=saved.grade.value,
            )
        )
        return saved


certification_service = CertificationService()
