"""Customs, Border Control & International Trade facade — Sprint 15.4."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.customs_trade.customs import BorderControl, CustomsManagement
from applications.port_enterprise.customs_trade.services import (
    AITradeIntelligence,
    CustomsDashboard,
    CustomsKnowledge,
)
from applications.port_enterprise.customs_trade.trade import (
    ComplianceManagement,
    DocumentManagement,
    InternationalTrade,
)
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class CustomsTradeSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.customs = CustomsManagement(self.store)
        self.border = BorderControl(self.store)
        self.trade = InternationalTrade(self.store)
        self.compliance = ComplianceManagement(self.store)
        self.documents = DocumentManagement(self.store)
        self.ai = AITradeIntelligence(self.store)
        self.dashboard = CustomsDashboard(self.store)
        self.knowledge = CustomsKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        office = self.customs.register_office(name="Odessa Customs", code="UAODS", country="UA")
        hs = self.customs.register_hs_code(code="8703.23", description="Motor cars", duty_rate=0.1)
        self.customs.set_tariff(hs_code=hs["code"], country="UA", rate=0.1)
        decl = self.customs.declare(
            declaration_type="import",
            reference="DEC-BOOT-001",
            office_id=office["office_id"],
            hs_code=hs["code"],
            value=120000,
        )
        duty = self.customs.calculate_duty(declaration_id=decl["declaration_id"], duty_rate=0.1, tax_rate=0.2)
        clearance = self.customs.clear(decl["declaration_id"], status="cleared")

        cp = self.border.register_checkpoint(name="Odessa Border Gate", border="UA-MD")
        self.border.inspect_cargo(checkpoint_id=cp["checkpoint_id"], cargo_ref="CARGO-1")
        self.border.inspect_vehicle(checkpoint_id=cp["checkpoint_id"], plate="AA1111BB")
        self.border.inspect_container(checkpoint_id=cp["checkpoint_id"], container_ref="MSCU1234567")
        self.border.verify_seal(container_ref="MSCU1234567", seal_no="SEAL-9001")
        self.border.risk_inspect(checkpoint_id=cp["checkpoint_id"], subject_ref="TRK-1", risk_score=0.35)
        crossing = self.border.crossing(
            checkpoint_id=cp["checkpoint_id"], direction="in", subject_ref="TRK-1"
        )

        self.trade.register_country(code="UA", name="Ukraine")
        self.trade.register_country(code="TR", name="Turkey")
        partner = self.trade.register_partner(name="Black Sea Trading", country="TR", role="seller")
        self.trade.trade_agreement(name="UA-TR Preferential", parties=["UA", "TR"])
        imp = self.trade.register_import(reference="IMP-001", origin_country="TR", value=120000)
        exp = self.trade.register_export(reference="EXP-001", destination_country="PL", value=45000)
        self.trade.set_incoterm(trade_ref=imp["import_id"], incoterm="CIF")
        self.trade.letter_of_credit(reference="LC-7788", amount=120000, bank="Port Bank")
        self.trade.commercial_invoice(trade_ref=imp["import_id"], amount=120000, currency="USD")
        self.trade.packing_list(trade_ref=imp["import_id"], packages=40, weight_kg=28000)

        self.compliance.screen_sanctions(party_name=partner["name"], country="TR")
        self.compliance.register_restricted(hs_code="9301.00", reason="military")
        self.compliance.dual_use(item_ref="ITEM-DU-1", controlled=True)
        self.compliance.license(license_no="LIC-IMP-22", license_type="import", expires_at="2027-01-01")
        self.compliance.certificate(cert_type="origin", reference="COO-55", issuer="Chamber")
        self.compliance.audit(entity_type="declaration", entity_id=decl["declaration_id"], action="cleared")
        report = self.compliance.compliance_report(period="monthly")

        bl = self.documents.store_document(doc_type="bl", title="Bill of Lading", reference="BL-001")
        self.documents.store_document(doc_type="cmr", title="CMR Note", reference="CMR-001")
        self.documents.store_document(doc_type="rail_waybill", title="CIM", reference="RW-001")
        self.documents.store_document(doc_type="air_waybill", title="AWB", reference="AWB-001")
        self.documents.store_document(
            doc_type="certificate_of_origin", title="COO", reference="COO-55"
        )
        self.documents.store_document(doc_type="phytosanitary", title="Phyto", reference="PHY-1")
        self.documents.store_document(doc_type="veterinary", title="Vet Cert", reference="VET-1")
        sig = self.documents.sign(bl["document_id"], signer="Customs Officer")

        risk = self.ai.compliance_risk(party=partner["name"], score=0.22)
        self.ai.delay_predict(declaration_id=decl["declaration_id"], risk=0.18)
        self.ai.validate_document(document_id=bl["document_id"], valid=True)
        self.ai.optimize_trade(corridor="TR-UA")
        self.ai.optimize_tariff(hs_code=hs["code"], baseline_rate=0.1)
        self.ai.congestion_predict(checkpoint_id=cp["checkpoint_id"])
        fraud = self.ai.fraud_detect(trade_ref=imp["import_id"], anomaly_score=0.15)

        for rtype, key in (
            ("customs", decl["declaration_id"]),
            ("compliance", report["report_id"]),
            ("document", bl["document_id"]),
            ("international", imp["import_id"]),
            ("trade", partner["partner_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="customs")
        return {
            "bootstrap": True,
            "office_id": office["office_id"],
            "declaration_id": decl["declaration_id"],
            "duty_id": duty["calculation_id"],
            "clearance_id": clearance["clearance_id"],
            "checkpoint_id": cp["checkpoint_id"],
            "crossing_id": crossing["crossing_id"],
            "import_id": imp["import_id"],
            "export_id": exp["export_id"],
            "partner_id": partner["partner_id"],
            "report_id": report["report_id"],
            "document_id": bl["document_id"],
            "signature_id": sig["signature_id"],
            "risk_id": risk["scoring_id"],
            "fraud_id": fraud["detection_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "customs": self.customs.status(),
            "border": self.border.status(),
            "trade": self.trade.status(),
            "compliance": self.compliance.status(),
            "documents": self.documents.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


customs_trade = CustomsTradeSuite()
