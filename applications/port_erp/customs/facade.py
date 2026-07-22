# Customs facade — documentation, trade, broker, compliance, certificates, tariffs.

from __future__ import annotations

from typing import Any

from applications.port_erp.broker.engine import BrokerOperationsEngine, broker_operations_engine
from applications.port_erp.certificates.engine import CertificateManager, certificate_manager
from applications.port_erp.compliance.engine import ComplianceEngine, compliance_engine
from applications.port_erp.customs.engine import CustomsEngine, customs_engine
from applications.port_erp.documents.engine import CargoDocumentationEngine, cargo_documentation_engine
from applications.port_erp.incoterms.service import IncotermsService, incoterms_service
from applications.port_erp.inspection.engine import InspectionEngine, inspection_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.international_trade.engine import (
    InternationalTradeEngine,
    international_trade_engine,
)
from applications.port_erp.tariffs.engine import TariffEngine, tariff_engine


class CustomsDomainEngine:
    """Sprint 9.4 facade over customs, trade, documents, compliance."""

    def __init__(
        self,
        customs: CustomsEngine | None = None,
        documents: CargoDocumentationEngine | None = None,
        trade: InternationalTradeEngine | None = None,
        broker: BrokerOperationsEngine | None = None,
        inspection: InspectionEngine | None = None,
        compliance: ComplianceEngine | None = None,
        certificates: CertificateManager | None = None,
        tariffs: TariffEngine | None = None,
        incoterms: IncotermsService | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.customs = customs or customs_engine
        self.documents = documents or cargo_documentation_engine
        self.trade = trade or international_trade_engine
        self.broker = broker or broker_operations_engine
        self.inspection = inspection or inspection_engine
        self.compliance = compliance or compliance_engine
        self.certificates = certificates or certificate_manager
        self.tariffs = tariffs or tariff_engine
        self.incoterms = incoterms or incoterms_service
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "declarations": len(self.customs.list_declarations()),
            "documents": len(self.documents.list_documents()),
            "certificates": len(self.certificates.list_certificates()),
            "shipments": len(self.trade.list_shipments()),
            "broker_cases": len(self.broker.list_cases()),
            "inspections": len(self.inspection.list_inspections()),
            "compliance_checks": len(self.compliance.list_checks()),
            "tariffs": len(self.tariffs.list_tariffs()),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("customs:snapshot", self.metrics())


customs_domain_engine = CustomsDomainEngine()
