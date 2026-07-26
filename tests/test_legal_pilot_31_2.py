"""Tests — Legal Pilot Execution & Document Automation (Sprint 31.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes


ROOT = Path(__file__).resolve().parents[1]
LE = "/api/legal-enterprise/v1"
CM = "/api/legal-cm/v1"
DI = "/api/legal-di/v1"
CP = "/api/legal-cp/v1"
AA = "/api/legal-aa/v1"
EI = "/api/legal-ei/v1"

DOCS = [
    "LEGAL_PILOT_EXECUTION_31_2.md",
    "LEGAL_INTEGRATION_31_2.md",
    "DOCUMENT_WORKFLOW_31_2.md",
    "AI_LEGAL_GUIDE_31_2.md",
    "ECOSYSTEM_REUSE_MATRIX_31_2.md",
    "PRODUCTION_STATUS_31_2.md",
    "RELEASE_NOTES_31_2.md",
    "SPRINT_REPORT_31_2.md",
]


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    legal_enterprise.reset()
    yield
    platform_builder.reset()
    legal_enterprise.reset()


def test_legal_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "31.2" in path.read_text()


def test_platform_legal_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.46.0"
    assert health["sprint"] == "32.3.4"
    assert health["release_status"] == "Live Enterprise Activity & AI Operations"


@pytest.mark.asyncio
async def test_legal_case_and_document_automation(client):
    entity = await client.post(
        f"{LE}/registry",
        json={
            "action": "entity",
            "name": "Lee & Partners",
            "entity_type": "corporation",
            "jurisdiction": "US-DE",
        },
    )
    assert entity.status == 201

    client_reg = await client.post(
        f"{LE}/registry",
        json={
            "action": "individual",
            "full_name": "Alex Client",
            "national_id": "ID-31-2",
            "residency": "US-NY",
        },
    )
    assert client_reg.status == 201

    attorney = await client.post(
        f"{LE}/registry",
        json={
            "action": "attorney",
            "full_name": "Jordan Lee",
            "bar_number": "BAR-312",
            "firm": "Lee & Partners",
            "specializations": ["commercial"],
        },
    )
    assert attorney.status == 201

    customer = await client.post(
        f"{CP}/counterparties",
        json={"action": "customer", "name": "Alex Client", "country": "US", "risk_level": "medium"},
    )
    assert customer.status == 201

    company = await client.post(
        f"{CP}/governance",
        json={
            "action": "company",
            "name": "Alex Holdings",
            "jurisdiction": "US-DE",
            "registration_no": "DE-312",
            "structure": "corporation",
        },
    )
    assert company.status == 201

    intake = await client.post(
        f"{AA}/assistant",
        json={"action": "ask", "question": "Intake: unpaid commercial invoice dispute framing"},
    )
    assert intake.status == 201

    case = await client.post(
        f"{CM}/cases",
        json={
            "title": "Pilot Matter",
            "category": "commercial",
            "priority": "high",
            "status": "intake",
            "owner": "Jordan Lee",
            "court_name": "District Court",
            "case_number": "CV-2026-312",
        },
    )
    assert case.status == 201
    case_body = await case.json()
    case_id = case_body["case_id"]

    ai = await client.post(f"{CM}/ai", json={"action": "summary", "case_id": case_id})
    assert ai.status == 201

    template = await client.post(
        f"{DI}/contracts",
        json={
            "action": "template",
            "name": "Demand Template",
            "contract_type": "custom",
            "body": "Demand letter body",
            "clauses": [],
        },
    )
    assert template.status == 201
    template_body = await template.json()

    contract = await client.post(
        f"{DI}/contracts",
        json={
            "action": "nda",
            "title": "Mutual NDA",
            "parties": ["Alex Client", "Lee & Partners"],
            "template_id": template_body["template_id"],
        },
    )
    assert contract.status == 201

    draft = await client.post(
        f"{DI}/drafting",
        json={"action": "draft", "prompt": "Draft demand letter for unpaid invoice", "contract_type": "custom"},
    )
    assert draft.status == 201

    doc = await client.post(
        f"{CM}/documents",
        json={
            "case_id": case_id,
            "title": "Complaint",
            "document_type": "legal",
            "uri": "vault://legal/312",
            "version": "1.0",
        },
    )
    assert doc.status == 201
    doc_body = await doc.json()
    document_id = doc_body["document_id"]

    version = await client.post(
        f"{CM}/documents",
        json={"action": "version", "document_id": document_id, "version": "1.1", "summary": "revised"},
    )
    assert version.status == 201

    sign = await client.post(
        f"{CM}/documents",
        json={
            "action": "sign",
            "document_id": document_id,
            "signer": "Jordan Lee",
            "signature_ref": "sig://312",
        },
    )
    assert sign.status == 201

    approval = await client.post(
        f"{CM}/tasks",
        json={
            "action": "approval",
            "case_id": case_id,
            "item": "Complaint",
            "requester": "Jordan Lee",
            "approver": "GC",
        },
    )
    assert approval.status == 201

    hearing = await client.post(
        f"{CM}/calendar",
        json={
            "case_id": case_id,
            "title": "Preliminary Hearing",
            "scheduled_at": "2026-08-14T10:00:00Z",
            "judge_name": "Hon. Ellis",
            "hearing_type": "hearing",
        },
    )
    assert hearing.status == 201

    task = await client.post(
        f"{CM}/tasks",
        json={
            "case_id": case_id,
            "title": "Prepare brief",
            "assignee": "Jordan Lee",
            "priority": "high",
            "due_on": "2026-08-10",
        },
    )
    assert task.status == 201

    deadline = await client.post(
        f"{CM}/deadlines",
        json={
            "case_id": case_id,
            "deadline_type": "filing",
            "due_on": "2026-07-30",
            "title": "File response",
            "risk": "high",
        },
    )
    assert deadline.status == 201

    await client.post(f"{EI}/bootstrap", json={})
    assert (await client.get(f"{CM}/dashboard?type=case")).status == 200
    assert (await client.get(f"{EI}/dashboard?type=executive")).status == 200
    assert (await client.get(f"{LE}/dashboard?type=legal")).status == 200


def test_prior_pilots_unchanged_routes():
    web = ROOT / "src" / "web"
    app = (web / "src" / "App.tsx").read_text()
    for needle in (
        'path="/workspace/auto"',
        "AutomotiveLiveWorkflowPage",
        'path="/workspace/beauty"',
        "BeautyLiveWorkflowPage",
        'path="/workspace/cafe"',
        "CafeLiveWorkflowPage",
        'path="/workspace/agro"',
        "AgricultureLiveWorkflowPage",
        'path="/workspace/legal"',
        "LegalLiveWorkflowPage",
    ):
        assert needle in app, needle
    assert (web / "workspace" / "legal" / "legalWorkflow.ts").exists()
    assert (web / "workspace" / "agriculture" / "agricultureWorkflow.ts").exists()


def test_legal_web_and_reuse_matrix():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "legal" / "legalWorkflow.ts").read_text()
    for needle in (
        "law_firm_crm",
        "ai_intake",
        "case_creation",
        "document_generation",
        "calendar",
        "tasks",
        "stepAiTeamConfigure",
        "quality_gates",
        "runLegalLiveWorkflow",
        "legalCasePrefix",
        "legalDocumentsPrefix",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.3.4"' in cfg
    assert "legalEnterprisePrefix" in cfg
    assert "legalCasePrefix" in cfg
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "legal: true" in tmpl
    assert "shared_documents" in tmpl
    assert "CROSS_ECOSYSTEM_PATTERNS" in tmpl
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "legalCase" in hub
    assert "legalAi" in hub


def test_reuse_docs_and_manifest():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_31_2.md").read_text()
    assert "100%" in text
    assert "Legal" in text
    report = (ROOT / "docs" / "SPRINT_REPORT_31_2.md").read_text()
    assert "Drone" in report
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.46.0"' in manifest
    assert "32.3.4" in manifest
    assert "Live Enterprise Activity & AI Operations" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "LEGAL_PILOT_EXECUTION_31_2" in index
