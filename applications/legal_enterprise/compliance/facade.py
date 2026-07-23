"""Compliance Suite facade — Sprint 17.5."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.compliance.ai_compliance import AIComplianceIntelligence
from applications.legal_enterprise.compliance.aml import SanctionsAML
from applications.legal_enterprise.compliance.compliance_mgmt import ComplianceManagement
from applications.legal_enterprise.compliance.counterparties import CounterpartyDueDiligence
from applications.legal_enterprise.compliance.governance import CorporateGovernance
from applications.legal_enterprise.compliance.licenses import LicenseManagement
from applications.legal_enterprise.compliance.risk import LegalRiskManagement
from applications.legal_enterprise.compliance.services import ComplianceDashboard, ComplianceKnowledge
from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class ComplianceSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.governance = CorporateGovernance(self.store)
        self.compliance = ComplianceManagement(self.store)
        self.licenses = LicenseManagement(self.store)
        self.counterparties = CounterpartyDueDiligence(self.store)
        self.aml = SanctionsAML(self.store)
        self.risk = LegalRiskManagement(self.store)
        self.ai = AIComplianceIntelligence(self.store)
        self.dashboard = ComplianceDashboard(self.store)
        self.knowledge = ComplianceKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        parent = self.governance.register_company(
            name="LexCorp Holdings", jurisdiction="US-DE", registration_no="DE-1001"
        )
        sub = self.governance.register_company(
            name="LexCorp Trading LLC", jurisdiction="US-NY", structure="llc"
        )
        self.governance.register_structure(
            company_id=sub["company_id"], parent_id=parent["company_id"], relation="subsidiary"
        )
        sh = self.governance.register_shareholder(
            company_id=parent["company_id"], name="Founder Trust", ownership_pct=60
        )
        board = self.governance.register_board_member(
            company_id=parent["company_id"], name="Sam Rivera", role="chair"
        )
        exec_ = self.governance.register_executive(
            company_id=parent["company_id"], name="Alex Morgan", title="CEO"
        )
        corp_doc = self.governance.register_document(
            company_id=parent["company_id"], title="Bylaws", document_type="bylaws"
        )
        resolution = self.governance.register_resolution(
            company_id=parent["company_id"],
            title="Approve Compliance Framework",
            adopted_on="2026-01-15",
        )

        fw = self.compliance.register_framework(name="Enterprise Compliance Framework", jurisdiction="national")
        req = self.compliance.register_requirement(
            framework_id=fw["framework_id"], code="CF-01", title="Data protection controls"
        )
        chk = self.compliance.checklist_item(
            requirement_id=req["requirement_id"], company_id=parent["company_id"], status="open"
        )
        self.compliance.track_status(checklist_id=chk["checklist_id"], status="in_progress", note="controls mapping")
        policy = self.compliance.register_policy(title="Code of Conduct", policy_type="internal")
        control = self.compliance.register_control(
            name="Access review control", control_type="detective", policy_id=policy["policy_id"]
        )
        exc = self.compliance.register_exception(
            control_id=control["control_id"], reason="Temporary vendor exception", approved_by="GC"
        )

        lic = self.licenses.register_license(
            name="Financial Services License", issuer="Regulator", expires_on="2026-12-31", company_id=parent["company_id"]
        )
        permit = self.licenses.register_permit(name="Trade Permit", issuer="City", expires_on="2026-09-01")
        cert = self.licenses.register_certificate(name="ISO 27001", issuer="CertBody", expires_on="2027-01-01")
        self.licenses.monitor_expiration(license_id=lic["license_id"])
        renewal = self.licenses.start_renewal(target_id=lic["license_id"], kind="license", due_on="2026-11-01")
        ntf = self.licenses.notify_renewal(renewal_id=renewal["renewal_id"])

        vendor = self.counterparties.register_vendor(name="Acme Ops", country="US", risk_level="medium")
        customer = self.counterparties.register_customer(name="Contoso Trading LLC", country="US")
        partner = self.counterparties.register_partner(name="Global Partner AG", country="CH")
        kyc = self.counterparties.run_kyc(counterparty_id=vendor["counterparty_id"])
        kyb = self.counterparties.run_kyb(counterparty_id=customer["counterparty_id"])
        self.counterparties.classify_risk(counterparty_id=partner["counterparty_id"], risk_level="high")

        san = self.aml.monitor_sanctions(name="Contoso Trading LLC", list_name="OFAC", matched=False)
        pep = self.aml.register_pep(name="Foreign Official X", role="minister", country="XX")
        aml = self.aml.aml_score(counterparty_id=partner["counterparty_id"], score=72)
        self.aml.watchlist(name="Global Partner AG", list_name="internal", hit=True)
        hr = self.aml.detect_high_risk(entity_name="Global Partner AG", reason="elevated AML score")
        txn = self.aml.review_transaction(
            transaction_ref="TXN-1001", amount=250000, counterparty_id=partner["counterparty_id"], status="escalated"
        )

        risk = self.risk.register_risk(
            title="License lapse risk",
            category="licensing",
            likelihood="medium",
            impact="high",
            company_id=parent["company_id"],
        )
        assess = self.risk.assess_compliance_risk(
            title="Q3 compliance assessment", score=58, findings=["Open checklist items"]
        )
        self.risk.correlate_contract_risk(contract_ref="MSA-1", risk_id=risk["risk_id"], detail="vendor MSA")
        reg = self.risk.regulatory_change_impact(
            change_title="DPL amendment 2026", impact="high", detail="controller duties expanded"
        )
        heat = self.risk.heatmap()
        self.risk.prioritize(risk_id=risk["risk_id"], priority="high")
        mit = self.risk.recommend_mitigation(risk_id=risk["risk_id"])

        gap = self.ai.detect_gaps(company_id=parent["company_id"])
        self.ai.detect_policy_conflicts()
        self.ai.monitor_regulatory_change(change_title="DPL amendment 2026")
        health = self.ai.compliance_health_score()
        gov_score = self.ai.governance_score()
        rec = self.ai.recommend()
        report = self.ai.nl_report(audience="board")

        self.knowledge.publish(base="compliance", key=fw["framework_id"], payload={"name": fw["name"]})
        self.knowledge.publish(base="corporate", key=parent["company_id"], payload={"name": parent["name"]})
        self.knowledge.publish(base="license", key=lic["license_id"], payload={"name": lic["name"]})
        self.knowledge.publish(base="policy", key=policy["policy_id"], payload={"title": policy["title"]})
        self.knowledge.publish(base="risk", key=risk["risk_id"], payload={"title": risk["title"]})

        dash = self.dashboard.render(dashboard_type="compliance")
        return {
            "bootstrap": True,
            "company_id": parent["company_id"],
            "subsidiary_id": sub["company_id"],
            "shareholder_id": sh["shareholder_id"],
            "board_id": board["board_id"],
            "executive_id": exec_["executive_id"],
            "corp_doc_id": corp_doc["document_id"],
            "resolution_id": resolution["resolution_id"],
            "framework_id": fw["framework_id"],
            "requirement_id": req["requirement_id"],
            "checklist_id": chk["checklist_id"],
            "policy_id": policy["policy_id"],
            "control_id": control["control_id"],
            "exception_id": exc["exception_id"],
            "license_id": lic["license_id"],
            "permit_id": permit["permit_id"],
            "certificate_id": cert["certificate_id"],
            "renewal_id": renewal["renewal_id"],
            "notification_id": ntf["notification_id"],
            "vendor_id": vendor["counterparty_id"],
            "customer_id": customer["counterparty_id"],
            "partner_id": partner["counterparty_id"],
            "kyc_id": kyc["kyc_id"],
            "kyb_id": kyb["kyb_id"],
            "sanctions_id": san["screening_id"],
            "pep_id": pep["pep_id"],
            "aml_id": aml["aml_id"],
            "high_risk_id": hr["detection_id"],
            "txn_id": txn["review_id"],
            "risk_id": risk["risk_id"],
            "assessment_id": assess["assessment_id"],
            "reg_change_id": reg["change_id"],
            "heatmap_id": heat["heatmap_id"],
            "mitigation_id": mit["mitigation_id"],
            "gap_id": gap["insight_id"],
            "health_id": health["insight_id"],
            "governance_score_id": gov_score["insight_id"],
            "recommend_id": rec["insight_id"],
            "report_id": report["insight_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "governance": self.governance.status(),
            "compliance": self.compliance.status(),
            "licenses": self.licenses.status(),
            "counterparties": self.counterparties.status(),
            "aml": self.aml.status(),
            "risk": self.risk.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


compliance = ComplianceSuite()
