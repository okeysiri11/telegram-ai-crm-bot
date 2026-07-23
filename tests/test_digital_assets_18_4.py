"""Tests — Digital Asset Treasury (Sprint 18.4)."""

from __future__ import annotations

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


def test_version_digital_assets_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.7-enterprise"
    assert health["digital_asset_treasury_ready"] is True
    assert health["crypto_finance_integration_ready"] is True
    assert health["crypto_accounting_ready"] is True
    assert health["ai_digital_asset_intelligence_ready"] is True
    assert health["treasury_platform_ready"] is True
    assert health["engines"]["digital_assets"] == "1.0"


def test_wallets_and_accounting():
    suite = finance_enterprise.digital_assets
    hot = suite.wallets.create_wallet(label="QA Hot", wallet_type="hot", network="ethereum")
    suite.wallets.add_address(wallet_id=hot["wallet_id"], address="0xqa")
    suite.wallets.update_balance(wallet_id=hot["wallet_id"], balance=1.5, asset="ETH")
    suite.accounting.post_ledger(
        asset_symbol="ETH", quantity=1.5, unit_cost=3000, side="buy", wallet_id=hot["wallet_id"]
    )
    cb = suite.accounting.cost_basis(asset_symbol="ETH")
    assert cb["average_cost"] == 3000
    assert suite.accounting.realized_pnl(
        asset_symbol="ETH", sell_quantity=0.5, sell_price=3500, average_cost=3000
    )["realized_pnl"] == 250
    with pytest.raises(ValidationError):
        suite.wallets.create_wallet(label="", wallet_type="hot", network="ethereum")


def test_exchange_treasury_ai_bootstrap():
    suite = finance_enterprise.digital_assets
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.2.0-enterprise"
    assert boot["hot_wallet_id"] and boot["link_id"] and boot["ai_nl_id"]
    assert suite.exchange.status()["links"] >= 1
    assert suite.operations.status()["operations"] >= 1
    assert suite.ai.nl_report(audience="board")["insight_type"] == "nl_report"
    for dtype in ("digital_assets", "treasury", "portfolio", "wallets", "exchange"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_digital_assets(client):
    health = await client.get(f"{DA}/health")
    body = await health.json()
    assert body["application_version"] == "5.2.0-enterprise"
    assert body["digital_asset_treasury_ready"] is True
    assert body["crypto_accounting_ready"] is True

    boot = await client.post(f"{DA}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    wal = await client.post(
        f"{DA}/wallets",
        json={"label": "API Hot", "wallet_type": "hot", "network": "polygon"},
    )
    assert wal.status == 201

    ai = await client.post(
        f"{DA}/ai",
        json={"action": "nl_report", "audience": "cfo"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, PAY, BIL, TR):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.2.0-enterprise"

    assert boot_body["eth_id"]


def test_docs_and_regression_18_4():
    for name in (
        "DIGITAL_ASSET_TREASURY.md",
        "CRYPTO_FINANCE_INTEGRATION.md",
        "CRYPTO_ACCOUNTING.md",
        "WALLET_MANAGEMENT.md",
        "DIGITAL_ASSET_RISK.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "DIGITAL_ASSET_TREASURY.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "digital_assets" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "treasury" / "facade.py").exists()

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
    assert "5.2.0-enterprise" in manifest
    assert "18.8" in manifest
