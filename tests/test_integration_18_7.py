"""Tests — Enterprise Financial Integration (Sprint 18.7)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.register import register_finance_enterprise_routes
from applications.finance_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/finance-enterprise/v1"
PAY = "/api/finance-pay/v1"
BIL = "/api/finance-bil/v1"
TR = "/api/finance-tr/v1"
DA = "/api/finance-da/v1"
RPT = "/api/finance-rpt/v1"
CFO = "/api/finance-cfo/v1"
INT = "/api/finance-int/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_finance_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    finance_enterprise.reset()
    yield
    finance_enterprise.reset()


def test_version_integration_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.6-enterprise"
    assert health["enterprise_financial_integration_ready"] is True
    assert health["cross_platform_operations_ready"] is True
    assert health["financial_event_bus_ready"] is True
    assert health["ai_enterprise_finance_ready"] is True
    assert health["ai_cfo_ready"] is True
    assert health["engines"]["integration"] == "1.0"


def test_event_bus_and_platforms():
    suite = finance_enterprise.integration
    suite.event_bus.register_event_type(name="qa.sale", platform="automotive")
    evt = suite.event_bus.publish(
        platform="automotive", event_kind="transaction", amount=100, reference="QA-1"
    )
    replay = suite.event_bus.replay(event_id=evt["event_id"])
    assert replay["status"] == "replayed"
    op = suite.automotive.operate(operation="vehicle_sales", amount=1000, reference="VIN-QA")
    assert op["platform"] == "automotive"
    with pytest.raises(ValidationError):
        suite.agro.operate(operation="unknown_op", amount=1)


def test_ai_cross_platform_bootstrap():
    suite = finance_enterprise.integration
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.1.7-enterprise"
    assert boot["auto_sale_id"] and boot["crypto_settlement_id"] and boot["ai_nl_id"]
    assert suite.ai.nl_report(audience="board")["insight_type"] == "nl_report"
    assert suite.port.status()["operations"] >= 1
    assert suite.legal.status()["operations"] >= 1
    for dtype in (
        "enterprise_finance",
        "cross_platform",
        "operations",
        "revenue",
        "executive_integration",
    ):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_integration(client):
    health = await client.get(f"{INT}/health")
    body = await health.json()
    assert body["application_version"] == "5.1.7-enterprise"
    assert body["financial_event_bus_ready"] is True
    assert body["ai_enterprise_finance_ready"] is True

    boot = await client.post(f"{INT}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    plat = await client.post(
        f"{INT}/platforms",
        json={"platform": "port", "operation": "terminal_fee", "amount": 99},
    )
    assert plat.status == 201

    ai = await client.post(
        f"{INT}/ai",
        json={"action": "nl_report", "audience": "ceo"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, PAY, BIL, TR, DA, RPT, CFO):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.1.7-enterprise"

    assert boot_body["monitor_id"]


def test_performance_bootstrap():
    suite = finance_enterprise.integration
    started = time.perf_counter()
    boot = suite.bootstrap()
    elapsed = time.perf_counter() - started
    assert boot["bootstrap"] is True
    assert elapsed < 2.0


def test_docs_and_regression_18_7():
    for name in (
        "ENTERPRISE_FINANCIAL_INTEGRATION.md",
        "CROSS_PLATFORM_FINANCE.md",
        "FINANCIAL_EVENT_BUS.md",
        "ENTERPRISE_OPERATIONS.md",
        "AI_ENTERPRISE_FINANCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_FINANCIAL_INTEGRATION.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "integration" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "ai_cfo" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    manifest = (ROOT / "applications" / "finance_enterprise" / "manifest.json").read_text()
    assert "5.1.7-enterprise" in manifest
    assert "18.7" in manifest
