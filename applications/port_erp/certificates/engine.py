# Certificate Manager — origin, phyto, veterinary, quality, insurance.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.customs.events import CertificateIssuedEvent
from applications.port_erp.customs.models import CertificateType, DocumentStatus, TradeCertificate
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class CertificateManager:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def certificate_types(self) -> list[str]:
        return [t.value for t in CertificateType]

    def create(self, certificate: TradeCertificate) -> TradeCertificate:
        if not certificate.title:
            certificate.title = certificate.certificate_type.value.replace("_", " ").title()
        return self._store.trade_certificates.save(certificate.certificate_id, certificate)

    def get(self, certificate_id: str) -> TradeCertificate:
        cert = self._store.trade_certificates.get(certificate_id)
        if cert is None:
            raise NotFoundError("TradeCertificate", certificate_id)
        return cert

    def list_certificates(
        self,
        *,
        shipment_id: str | None = None,
        cargo_id: str | None = None,
    ) -> list[TradeCertificate]:
        items = self._store.trade_certificates.list_all()
        if shipment_id:
            items = [c for c in items if c.shipment_id == shipment_id]
        if cargo_id:
            items = [c for c in items if c.cargo_id == cargo_id]
        return items

    async def issue(self, certificate_id: str, *, issuer: str = "") -> TradeCertificate:
        cert = self.get(certificate_id)
        if not issuer and not cert.issuer:
            raise ValidationError("issuer is required")
        cert.issuer = issuer or cert.issuer
        cert.status = DocumentStatus.ISSUED
        cert.issued_at = time.time()
        saved = self._store.trade_certificates.save(certificate_id, cert)
        await publish(
            CertificateIssuedEvent(
                certificate_id=certificate_id,
                certificate_type=saved.certificate_type.value,
                cargo_id=saved.cargo_id,
            )
        )
        return saved


certificate_manager = CertificateManager()
