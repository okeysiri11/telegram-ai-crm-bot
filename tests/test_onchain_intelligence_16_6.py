"""Tests — On-Chain Intelligence (Sprint 16.6)."""

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
TA = "/api/crypto-ta/v1"
MM = "/api/crypto-mm/v1"
MI = "/api/crypto-mi/v1"
SE = "/api/crypto-se/v1"
RM = "/api/crypto-rm/v1"
OC = "/api/crypto-oc/v1"


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


def test_version_onchain_intelligence_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.7.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.5-enterprise"
    assert health["onchain_intelligence_ready"] is True
    assert health["whale_intelligence_ready"] is True
    assert health["blockchain_analytics_ready"] is True
    assert health["institution_monitoring_ready"] is True
    assert health["ai_onchain_intelligence_ready"] is True
    assert health["risk_management_ready"] is True


def test_blockchain_and_wallets():
    suite = crypto_enterprise.onchain_intelligence
    eth = suite.chains.connect(chain="ethereum")
    assert eth["status"] == "connected"
    multi = suite.chains.multi_chain()
    assert multi["count"] >= 9
    whale = suite.wallets.register(
        address="0xabc",
        chain="ethereum",
        wallet_type="whale",
        balance_usd=10_000_000,
    )
    assert whale["wallet_type"] == "whale"
    with pytest.raises(ValidationError):
        suite.chains.connect(chain="unknown")


def test_transactions_and_stablecoins():
    suite = crypto_enterprise.onchain_intelligence
    tx = suite.transactions.monitor(
        chain="ethereum",
        tx_hash="0x1",
        from_addr="a",
        to_addr="b",
        amount_usd=2_000_000,
    )
    assert tx["tx_id"]
    large = suite.transactions.large_transfer(chain="ethereum", amount_usd=2_000_000, asset="ETH")
    assert large["flagged"] is True
    flow = suite.stablecoins.flow(
        stablecoin="USDT",
        direction="inflow",
        amount_usd=50_000_000,
        chain="tron",
    )
    assert flow["stablecoin"] == "USDT"
    tvl = suite.defi.tvl(protocol="Aave", chain="ethereum", tvl_usd=1e9)
    assert tvl["tvl_usd"] == 1e9


def test_onchain_ai_and_bootstrap():
    suite = crypto_enterprise.onchain_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.7.6-enterprise"
    assert boot["whale_wallet_id"] and boot["tx_id"] and boot["report_id"]
    whale_ai = suite.ai.whale_activity(chain="bitcoin", intensity=0.9, side="accumulate")
    assert whale_ai["detected"] is True
    for dtype in ("onchain", "whale", "stablecoin", "defi", "institution", "ai_blockchain"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_onchain_intelligence(client):
    health = await client.get(f"{OC}/health")
    body = await health.json()
    assert body["application_version"] == "4.7.6-enterprise"
    assert body["onchain_intelligence_ready"] is True
    assert body["ai_onchain_intelligence_ready"] is True

    boot = await client.post(f"{OC}/bootstrap", json={})
    assert boot.status == 201

    wallet = await client.post(
        f"{OC}/wallets",
        json={
            "address": "0xqa",
            "chain": "solana",
            "wallet_type": "smart_money",
            "balance_usd": 1_000_000,
        },
    )
    assert wallet.status == 201

    ai = await client.post(
        f"{OC}/ai",
        json={"action": "health", "chain": "ethereum", "score": 80},
    )
    assert ai.status == 201

    for path in (PREFIX, TA, MM, MI, SE, RM):
        resp = await client.get(f"{path}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.7.6-enterprise"


def test_docs_and_regression_16_6():
    for name in (
        "ONCHAIN_ANALYTICS.md",
        "WHALE_INTELLIGENCE.md",
        "BLOCKCHAIN_MONITORING.md",
        "STABLECOIN_ANALYSIS.md",
        "DEFI_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_ONCHAIN_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "onchain_intelligence" / "facade.py").exists()

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
    assert "4.7.6-enterprise" in manifest
    assert "16.6" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "risk_management" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "strategy_engine" / "facade.py").exists()
