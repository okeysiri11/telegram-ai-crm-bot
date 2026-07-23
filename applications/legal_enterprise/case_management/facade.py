"""Case Management Suite facade — Sprint 17.3."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.case_management.ai_workflow import AILegalWorkflow
from applications.legal_enterprise.case_management.calendar import CourtCalendar
from applications.legal_enterprise.case_management.cases import CasePlatform
from applications.legal_enterprise.case_management.deadlines import ProceduralTimeline
from applications.legal_enterprise.case_management.documents import DocumentManagement
from applications.legal_enterprise.case_management.services import (
    CaseManagementDashboard,
    CaseManagementKnowledge,
)
from applications.legal_enterprise.case_management.tasks import TaskManagement
from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class CaseManagementSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.cases = CasePlatform(self.store)
        self.calendar = CourtCalendar(self.store)
        self.deadlines = ProceduralTimeline(self.store)
        self.tasks = TaskManagement(self.store)
        self.documents = DocumentManagement(self.store)
        self.ai = AILegalWorkflow(self.store)
        self.dashboard = CaseManagementDashboard(self.store)
        self.knowledge = CaseManagementKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        case = self.cases.register(
            title="LexCorp v Contoso — Active Matter",
            case_number="CM-2026-001",
            category="commercial",
            priority="high",
            status="active",
            owner="Jordan Lee",
            court_name="Central Commercial Court",
        )
        related = self.cases.register(
            title="Related Discovery Dispute",
            case_number="CM-2026-001A",
            category="commercial",
            priority="medium",
            status="active",
            owner="Jordan Lee",
        )
        self.cases.relate_cases(
            case_id=case["case_id"], related_case_id=related["case_id"], relation="related"
        )
        self.cases.assign_owner(case_id=case["case_id"], owner="Jordan Lee")
        self.cases.set_priority(case_id=case["case_id"], priority="high")
        self.cases.add_timeline(case_id=case["case_id"], event="kickoff", detail="Matter opened")

        room = self.calendar.register_courtroom(name="Courtroom 3A", building="Justice Hall", capacity=40)
        hearing = self.calendar.schedule_hearing(
            case_id=case["case_id"],
            title="Preliminary Hearing",
            scheduled_at="2026-08-15T10:00:00Z",
            judge_name="Hon. Morgan Ellis",
            courtroom_id=room["courtroom_id"],
        )
        self.calendar.assign_judge(hearing_id=hearing["hearing_id"], judge_name="Hon. Morgan Ellis")
        rem = self.calendar.create_reminder(
            hearing_id=hearing["hearing_id"], remind_at="2026-08-14T09:00:00Z"
        )
        sync = self.calendar.sync_calendar(source="court_system")
        rec = self.calendar.recurring_event(
            case_id=case["case_id"], title="Status conference", cadence="monthly", next_at="2026-09-01"
        )

        dl_appeal = self.deadlines.register_deadline(
            case_id=case["case_id"],
            deadline_type="appeal",
            due_on="2026-09-30",
            title="Appeal window",
            risk="watch",
        )
        self.deadlines.register_deadline(
            case_id=case["case_id"],
            deadline_type="limitation",
            due_on="2027-03-15",
            title="Limitation period",
        )
        self.deadlines.register_deadline(
            case_id=case["case_id"],
            deadline_type="evidence",
            due_on="2026-08-01",
            title="Evidence submission",
            risk="high",
        )
        self.deadlines.register_deadline(
            case_id=case["case_id"],
            deadline_type="filing",
            due_on="2026-07-28",
            title="Court filing deadline",
            risk="high",
        )
        calc = self.deadlines.calculate_deadline(
            case_id=case["case_id"],
            deadline_type="procedural",
            from_date="2026-07-21T00:00:00Z",
            days=14,
        )
        alert = self.deadlines.risk_alert(
            deadline_id=dl_appeal["deadline_id"], severity="watch", message="Appeal window approaching"
        )

        task = self.tasks.create_task(
            case_id=case["case_id"],
            title="Prepare hearing brief",
            assignee="Jordan Lee",
            priority="high",
            due_on="2026-08-10",
        )
        self.tasks.assign(task_id=task["task_id"], assignee="Pat Kim")
        self.tasks.set_priority(task_id=task["task_id"], priority="critical")
        wf = self.tasks.automate_workflow(case_id=case["case_id"], workflow="commercial_litigation")
        apr = self.tasks.request_approval(
            case_id=case["case_id"], item="Settlement authority memo", requester="Jordan Lee", approver="GC"
        )

        doc = self.documents.register_document(
            case_id=case["case_id"], title="Complaint", document_type="legal"
        )
        evidence = self.documents.register_evidence(case_id=case["case_id"], title="MSA Exhibit")
        filing = self.documents.register_filing(case_id=case["case_id"], title="Notice of Hearing")
        self.documents.record_version(document_id=doc["document_id"], version="1.1", summary="caption fix")
        self.documents.secure_store(document_id=doc["document_id"], vault_ref="vault://cm/CM-2026-001/complaint")
        sig = self.documents.digital_signature(document_id=filing["document_id"], signer="Jordan Lee")

        risk = self.ai.deadline_risk(case_id=case["case_id"])
        missing = self.ai.missing_documents(case_id=case["case_id"])
        progress = self.ai.progress_analysis(case_id=case["case_id"])
        opt = self.ai.optimize_workflow(case_id=case["case_id"])
        next_a = self.ai.recommend_next_actions(case_id=case["case_id"])
        health = self.ai.health_score(case_id=case["case_id"])
        summary = self.ai.natural_language_summary(case_id=case["case_id"])

        self.knowledge.publish(base="case", key=case["case_id"], payload={"number": case["case_number"]})
        self.knowledge.publish(base="deadline", key=dl_appeal["deadline_id"], payload={"type": "appeal"})
        self.knowledge.publish(base="task", key=task["task_id"], payload={"title": task["title"]})
        self.knowledge.publish(base="document", key=doc["document_id"], payload={"title": doc["title"]})
        self.knowledge.publish(base="calendar", key=hearing["hearing_id"], payload={"title": hearing["title"]})

        dash = self.dashboard.render(dashboard_type="case")
        return {
            "bootstrap": True,
            "case_id": case["case_id"],
            "related_case_id": related["case_id"],
            "courtroom_id": room["courtroom_id"],
            "hearing_id": hearing["hearing_id"],
            "reminder_id": rem["reminder_id"],
            "sync_id": sync["sync_id"],
            "recurring_id": rec["recurring_id"],
            "deadline_id": dl_appeal["deadline_id"],
            "calc_deadline_id": calc["deadline_id"],
            "alert_id": alert["alert_id"],
            "task_id": task["task_id"],
            "workflow_id": wf["workflow_id"],
            "approval_id": apr["approval_id"],
            "document_id": doc["document_id"],
            "evidence_id": evidence["document_id"],
            "filing_id": filing["document_id"],
            "signature_id": sig["signature_id"],
            "risk_id": risk["insight_id"],
            "missing_id": missing["insight_id"],
            "progress_id": progress["insight_id"],
            "optimize_id": opt["insight_id"],
            "next_id": next_a["insight_id"],
            "health_id": health["insight_id"],
            "summary_id": summary["insight_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "cases": self.cases.status(),
            "calendar": self.calendar.status(),
            "deadlines": self.deadlines.status(),
            "tasks": self.tasks.status(),
            "documents": self.documents.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


case_management = CaseManagementSuite()
