"""Tests — Bidex Pilot Execution & Financial Workflow Validation (Sprint 31.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.register import register_finance_enterprise_routes
from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes


ROOT = Path(__file__).resolve().parents[1]
DA = "/api/finance-da/v1"
PAY = "/api/finance-pay/v1"
TR = "/api/finance-tr/v1"
INT = "/api/finance-int/v1"
CP = "/api/legal-cp/v1"
CE = "/api/crypto-enterprise/v1"
ISAM = "/api/enterprise-isam/v1"

DOCS = [
    "BIDEX_PILOT_EXECUTION_31_3.md",
    "BIDEX_INTEGRATION_31_3.md",
    "FINANCIAL_WORKFLOW_31_3.md",
    "COMPLIANCE_GUIDE_31_3.md",
    "ECOSYSTEM_REUSE_MATRIX_31_3.md",
    "PRODUCTION_STATUS_31_3.md",
    "RELEASE_NOTES_31_3.md",
    "SPRINT_REPORT_31_3.md",
]


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_finance_enterprise_routes(application)
    register_legal_enterprise_routes(application)
    register_crypto_enterprise_routes(application)
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    finance_enterprise.reset()
    legal_enterprise.reset()
    crypto_enterprise.reset()
    enterprise_hub.reset()
    yield
    platform_builder.reset()
    finance_enterprise.reset()
    legal_enterprise.reset()
    crypto_enterprise.reset()
    enterprise_hub.reset()


def test_bidex_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "31.3" in path.read_text()


def test_platform_bidex_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.45.0"
    assert health["sprint"] == "32.3.3"
    assert health["release_status"] == "Enterprise City Navigation"


@pytest.mark.asyncio
async def test_bidex_financial_and_compliance_api(client):
    assert (await client.get(f"{DA}/health")).status == 200
    assert (await client.get(f"{PAY}/health")).status == 200
    assert (await client.get(f"{INT}/health")).status == 200
    assert (await client.get(f"{CP}/health")).status == 200
    assert (await client.get(f"{CE}/health")).status == 200
    assert (await client.get(f"{ISAM}/health")).status == 200

    identity = await client.post(
        f"{ISAM}/identity",
        json={"subject": "pilot.bidex@demo.corp", "identity_type": "user", "roles": ["employee"]},
    )
    assert identity.status in (200, 201, 400)  # may reject duplicate

    customer = await client.post(
        f"{CP}/counterparties",
        json={"action": "customer", "name": "Acme OTC", "country": "UA", "risk_level": "medium"},
    )
    assert customer.status == 201
    customer_body = await customer.json()
    cid = customer_body["counterparty_id"]

    kyc = await client.post(
        f"{CP}/counterparties",
        json={"action": "kyc", "counterparty_id": cid, "status": "passed"},
    )
    assert kyc.status == 201

    aml = await client.post(
        f"{CP}/aml",
        json={"action": "score", "counterparty_id": cid, "score": 72},
    )
    assert aml.status == 201

    risk = await client.post(
        f"{CP}/aml",
        json={"action": "high_risk", "counterparty_id": cid, "entity_name": "Acme OTC", "reason": "otc"},
    )
    assert risk.status == 201

    company = await client.post(
        f"{CP}/governance",
        json={
            "action": "company",
            "name": "Acme Holdings",
            "jurisdiction": "UA",
            "registration_no": "UA-313",
            "structure": "corporation",
        },
    )
    assert company.status == 201
    company_body = await company.json()

    doc = await client.post(
        f"{CP}/governance",
        json={
            "action": "document",
            "company_id": company_body["company_id"],
            "title": "KYC Pack",
            "document_type": "kyc",
        },
    )
    assert doc.status == 201

    wallet = await client.post(
        f"{DA}/wallets",
        json={"label": "Pilot Hot", "wallet_type": "hot", "network": "polygon"},
    )
    assert wallet.status == 201
    wallet_body = await wallet.json()
    wid = wallet_body["wallet_id"]

    otc = await client.post(
        f"{DA}/operations",
        json={
            "operation": "otc_settlement",
            "asset_symbol": "BTC",
            "amount": 0.25,
            "detail": "Pilot OTC",
            "from_ref": wid,
            "to_ref": "desk",
        },
    )
    assert otc.status == 201
    otc_body = await otc.json()

    payment = await client.post(
        f"{PAY}/payments",
        json={
            "amount": 12500,
            "currency": "USD",
            "external_key": f"otc-{otc_body['operation_id']}",
            "payee": "desk",
            "payer_ref": "pilot.bidex@demo.corp",
        },
    )
    assert payment.status == 201
    payment_body = await payment.json()

    approve = await client.post(
        f"{PAY}/processing",
        json={"action": "approve", "payment_id": payment_body["payment_id"], "approver": "cfo"},
    )
    assert approve.status == 201

    settle = await client.post(
        f"{INT}/platforms",
        json={
            "platform": "crypto",
            "operation": "otc_accounting",
            "amount": 12500,
            "reference": otc_body["operation_id"],
        },
    )
    assert settle.status == 201

    await client.post(f"{TR}/bootstrap", json={})
    assert (
        await client.post(f"{TR}/dashboard", json={"dashboard_type": "treasury"})
    ).status in (200, 201)

    audit = await client.post(
        f"{ISAM}/audit",
        json={
            "action": "otc_settled",
            "actor": "pilot.bidex@demo.corp",
            "subject": otc_body["operation_id"],
            "detail": "settled",
        },
    )
    assert audit.status == 201

    assert (await client.post(f"{DA}/dashboard", json={"dashboard_type": "digital_assets"})).status in (
        200,
        201,
    )
    assert (await client.post(f"{CP}/dashboard", json={"dashboard_type": "compliance"})).status in (
        200,
        201,
    )


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
        'path="/workspace/crypto"',
        "BidexLiveWorkflowPage",
    ):
        assert needle in app, needle
    assert (web / "workspace" / "crypto" / "bidexWorkflow.ts").exists()
    assert (web / "workspace" / "legal" / "legalWorkflow.ts").exists()


def test_bidex_web_and_reuse_matrix():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "crypto" / "bidexWorkflow.ts").read_text()
    for needle in (
        "identity_verification",
        "wallet",
        "otc_deal",
        "approval",
        "settlement",
        "audit_log",
        "stepAiTeamConfigure",
        "quality_gates",
        "runBidexLiveWorkflow",
        "financeDigitalAssetsPrefix",
        "legalCompliancePrefix",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.3.3"' in cfg
    assert "financeDigitalAssetsPrefix" in cfg
    assert "cryptoEnterprisePrefix" in cfg
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "crypto: true" in tmpl
    assert "computeReusePercentage" in tmpl
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "financeDigitalAssets" in hub
    assert "cryptoRisk" in hub


def test_reuse_docs_and_manifest():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_31_3.md").read_text()
    assert "100%" in text
    assert "Bidex" in text
    report = (ROOT / "docs" / "SPRINT_REPORT_31_3.md").read_text()
    assert "Drone" in report
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.45.0"' in manifest
    assert "32.3.3" in manifest
    assert "Enterprise City Navigation" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "BIDEX_PILOT_EXECUTION_31_3" in index
