"""Tests — Crypto Intelligence Platform Foundation (Sprint 16.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from applications.crypto_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crypto-enterprise/v1"
PE = "/api/port-enterprise/v1"
PEC = "/api/port-enterprise-certification/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_crypto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    crypto_enterprise.reset()
    yield
    crypto_enterprise.reset()


def test_version_crypto_enterprise_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.8.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.7-enterprise"
    assert health["crypto_enterprise_foundation_ready"] is True
    assert health["exchange_integration_ready"] is True
    assert health["market_data_ready"] is True
    assert health["portfolio_platform_ready"] is True


def test_exchanges_and_markets():
    ex = crypto_enterprise.exchanges.integrate_binance()
    assert ex["exchange"]["exchange_code"] == "binance"
    spot = crypto_enterprise.markets.register_spot(
        symbol="ETHUSDT",
        base="ETH",
        quote="USDT",
        exchange_id=ex["exchange"]["exchange_id"],
    )
    ticker = crypto_enterprise.markets.ticker(symbol="ETHUSDT", last=3500.0)
    assert spot["market_id"] and ticker["last"] == 3500.0
    with pytest.raises(ValidationError):
        crypto_enterprise.exchanges.register_exchange(name="X", exchange_code="unknown")


def test_assets_and_portfolio():
    boot = crypto_enterprise.bootstrap()
    assert boot["binance_id"] and boot["portfolio_id"] and boot["btc_id"]
    assert crypto_enterprise.assets.status()["coins"] >= 1
    assert crypto_enterprise.portfolio.status()["portfolios"] >= 1
    assert crypto_enterprise.exchanges.status()["exchanges"] == 6
    with pytest.raises(ValidationError):
        crypto_enterprise.portfolio.allocate(
            portfolio_id=boot["portfolio_id"], asset="BTC", weight_pct=150
        )
    for dtype in ("exchange", "portfolio", "market", "asset"):
        assert crypto_enterprise.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_crypto_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.8.0-enterprise"
    assert body["exchange_integration_ready"] is True
    assert body["market_data_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ticker = await client.post(
        f"{PREFIX}/markets",
        json={"action": "ticker", "symbol": "BTCUSDT", "last": 69000},
    )
    assert ticker.status == 201

    pnl = await client.post(
        f"{PREFIX}/portfolio",
        json={
            "action": "pnl",
            "portfolio_id": boot_body["portfolio_id"],
            "realized": 100,
            "unrealized": 50,
        },
    )
    assert pnl.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=exchange")
    assert dash.status == 200


def test_docs_and_regression_16_0():
    for name in (
        "CRYPTO_ENTERPRISE.md",
        "EXCHANGE_INTEGRATION.md",
        "MARKET_DATA.md",
        "PORTFOLIO_MANAGEMENT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_ENTERPRISE.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "application.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "exchanges.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "crypto_enterprise" / "manifest.json").read_text()
    assert "4.8.0-enterprise" in manifest
    assert "16.8" in manifest
    # Prior Port routes remain registered in server (not modified package contents)
    assert (ROOT / "applications" / "port_enterprise" / "enterprise_certification" / "facade.py").exists()
    _ = (PE, PEC)
