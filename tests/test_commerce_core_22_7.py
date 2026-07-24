"""Tests — Enterprise Commerce Core (Sprint 24.8 / v7.8.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_commerce.models import INDUSTRIES, KPI_TARGETS, PRINCIPLES


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = [
    "/api/enterprise-hub/v1",
    "/api/enterprise-orch/v1",
    "/api/enterprise-kg/v1",
    "/api/enterprise-agents/v1",
    "/api/enterprise-comms/v1",
    "/api/enterprise-workflow/v1",
    "/api/enterprise-eip/v1",
    "/api/enterprise-edp/v1",
    "/api/enterprise-isam/v1",
    "/api/enterprise-obs/v1",
    "/api/enterprise-tenancy/v1",
    "/api/enterprise-aop/v1",
    "/api/enterprise-ats/v1",
    "/api/enterprise-ekp/v1",
    "/api/enterprise-aios/v1",
    "/api/enterprise-evp/v1",
    "/api/enterprise-sdp/v1",
    "/api/enterprise-edf/v1",
    "/api/enterprise-edt/v1",
    "/api/enterprise-esi/v1",
    "/api/enterprise-epm/v1",
    "/api/enterprise-ebc/v1",
    "/api/enterprise-ecc/v1",
    "/api/enterprise-eas/v1",
    "/api/enterprise-edc/v1",
    "/api/enterprise-esh/v1",
    "/api/enterprise-eqa/v1",
    "/api/enterprise-edo/v1",
    "/api/enterprise-epf/v1",
    "/api/enterprise-erl/v1",
    "/api/enterprise-epi/v1",
    "/api/enterprise-aba/v1",
    "/api/enterprise-bos/v1",
    "/api/enterprise-bws/v1",
    "/api/enterprise-bcj/v1",
    "/api/enterprise-amo/v1",
    "/api/enterprise-ech/v1",
]
ECO = "/api/enterprise-eco/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


def test_version_eco_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.8.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.7.0"
    assert health["commerce_core_ready"] is True
    assert health["pos_ready"] is True
    assert health["loyalty_commerce_ready"] is True
    assert health["payment_gateway_ready"] is True
    assert health["engines"]["commerce_core"] == "1.0"
    assert set(PRINCIPLES)
    assert KPI_TARGETS["sale_under_20s"] is True
    assert "beauty" in INDUSTRIES and "retail" in INDUSTRIES


def test_sales_certs_memberships_loyalty_payments():
    suite = enterprise_hub.commerce_core
    pos = suite.open_pos(cashier_id="desk1", industry="beauty")
    assert pos["fast_checkout"] is True
    sale = suite.create_sale(
        lines=[
            {"kind": "service", "name": "Manicure", "price": 35, "materials": [{"sku": "polish", "qty": 1}]},
            {"kind": "product", "name": "Oil", "sku": "oil-1", "price": 15, "qty": 1},
        ],
        payments=[{"method": "cash", "amount": 30}, {"method": "card", "amount": 20}],
        customer_id="c_shop",
        mode="full",
    )
    assert sale["under_20s"] is True
    assert sale["mixed_payment"] is True
    assert sale["inventory"]["auto_deducted"] is True
    cert = suite.issue_certificate(face_value=50, customer_id="c_shop")
    assert cert["status"] == "active"
    redeemed = suite.redeem_certificate(certificate_id=cert["certificate_id"], amount=20)
    assert redeemed["balance"] == 30
    mem = suite.create_membership(customer_id="c_shop", visits_limit=5)
    assert mem["visits_remaining"] == 5
    loy = suite.loyalty_profile(customer_id="c_shop", points=60)
    assert loy["level"] == "bronze"
    pay = suite.charge(provider="apple_pay", amount=10, currency="USD")
    assert pay["pluggable"] is True
    advice = suite.advise()
    assert advice["proposes_only"] is True
    assert advice["ai_may_act"] is False
    with pytest.raises(ValidationError):
        suite.create_sale(lines=[], payments=[])


def test_bootstrap_commerce():
    suite = enterprise_hub.commerce_core
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.8.0"
    assert boot["commerce_core_ready"] is True
    assert boot["sale_under_20s"] is True
    assert boot["mixed_payment"] is True
    assert boot["ai_may_act"] is False
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["integrations"]["universal"] is True


@pytest.mark.asyncio
async def test_api_eco(client):
    health = await client.get(f"{ECO}/health")
    body = await health.json()
    assert body["application_version"] == "7.8.0"
    assert body["commerce_core_ready"] is True

    boot = await client.post(f"{ECO}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["commerce_core_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.8.0"


def test_docs_and_regression_22_7():
    for name in (
        "ENTERPRISE_COMMERCE_CORE.md",
        "ECO_SALES_POS.md",
        "ECO_CERTS_MEMBERSHIPS_LOYALTY.md",
        "ECO_INVENTORY_PAYMENTS_ADVISOR.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_COMMERCE_CORE.md").exists()
    assert (ROOT / "platform_enterprise_commerce" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "commerce_core" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS_CFG.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "7.8.0"' in manifest
    assert "24.8" in manifest
