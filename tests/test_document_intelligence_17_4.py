"""Tests — Document Intelligence (Sprint 17.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
JI = "/api/legal-ji/v1"
CM = "/api/legal-cm/v1"
DI = "/api/legal-di/v1"


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
    legal_enterprise.reset()
    yield
    legal_enterprise.reset()


def test_version_document_intelligence_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "5.0.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.7-enterprise"
    assert health["contract_builder_ready"] is True
    assert health["document_intelligence_ready"] is True
    assert health["ai_risk_review_ready"] is True
    assert health["legal_drafting_ready"] is True
    assert health["case_management_ready"] is True


def test_contracts_and_ocr():
    suite = legal_enterprise.document_intelligence
    clause = suite.contracts.add_clause(title="NDA Core", kind="confidentiality", mandatory=True)
    nda = suite.contracts.generate_nda(title="QA NDA", clause_ids=[clause["clause_id"]])
    assert nda["contract_type"] == "nda"
    pdf = suite.ingest.import_document(title="Scan", format="pdf", content="confidentiality terms")
    ocr = suite.ingest.run_ocr(document_id=pdf["document_id"])
    assert ocr["confidence"] >= 0.9
    with pytest.raises(ValidationError):
        suite.contracts.generate(contract_type="unknown", title="X")


def test_risk_comparison_drafting_bootstrap():
    suite = legal_enterprise.document_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.0.0-enterprise"
    assert boot["nda_id"] and boot["ocr_id"] and boot["risk_score_id"] and boot["draft_id"]
    assert suite.risk.risk_score(contract_id=boot["custom_id"])["kind"] == "score"
    assert suite.drafting.summarize(prompt="short doc")["kind"] == "summary"
    for dtype in ("contract", "document", "risk", "ai_review"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_document_intelligence(client):
    health = await client.get(f"{DI}/health")
    body = await health.json()
    assert body["application_version"] == "5.0.0-enterprise"
    assert body["contract_builder_ready"] is True
    assert body["document_intelligence_ready"] is True

    boot = await client.post(f"{DI}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    risk = await client.post(
        f"{DI}/risk",
        json={"action": "score", "contract_id": boot_body["sales_id"]},
    )
    assert risk.status == 201

    draft = await client.post(
        f"{DI}/drafting",
        json={"action": "negotiate", "prompt": "Push for mutual indemnity"},
    )
    assert draft.status == 201

    ocr = await client.post(
        f"{DI}/ingest",
        json={"action": "ocr", "document_id": boot_body["pdf_id"]},
    )
    assert ocr.status == 201

    for prefix in (PREFIX, LI, JI, CM):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.0.0-enterprise"


def test_docs_and_regression_17_4():
    for name in (
        "CONTRACT_BUILDER.md",
        "DOCUMENT_INTELLIGENCE.md",
        "AI_RISK_REVIEW.md",
        "CLAUSE_LIBRARY.md",
        "LEGAL_DOCUMENT_AUTOMATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "DOCUMENT_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "document_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "case_management" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    manifest = (ROOT / "applications" / "legal_enterprise" / "manifest.json").read_text()
    assert "5.0.0-enterprise" in manifest
    assert "17.8" in manifest
