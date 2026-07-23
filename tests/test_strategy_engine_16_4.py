"""Tests — Strategy Engine (Sprint 16.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crypto-enterprise/v1"
TA = "/api/crypto-ta/v1"
MM = "/api/crypto-mm/v1"
MI = "/api/crypto-mi/v1"
SE = "/api/crypto-se/v1"


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


def test_version_strategy_engine_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.8.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.7-enterprise"
    assert health["strategy_builder_ready"] is True
    assert health["backtesting_engine_ready"] is True
    assert health["signal_generation_ready"] is True
    assert health["ai_strategy_intelligence_ready"] is True
    assert health["portfolio_simulation_ready"] is True
    assert health["news_intelligence_ready"] is True


def test_strategy_and_backtesting():
    suite = crypto_enterprise.strategy_engine
    strategy = suite.builder.from_template(template="breakout", name="BTC Breakout", symbol="BTCUSDT")
    assert strategy["strategy_id"]
    rule = suite.builder.add_rule(
        strategy_id=strategy["strategy_id"],
        condition_type="indicator",
        expression="close > bb_upper",
    )
    assert rule["rule_id"]
    bt = suite.backtesting.run(
        strategy_id=strategy["strategy_id"],
        from_ts="2025-01-01T00:00:00Z",
        to_ts="2026-01-01T00:00:00Z",
    )
    assert bt["backtest_id"]
    perf = suite.performance.compute(backtest_id=bt["backtest_id"])
    assert perf["metrics"]["sharpe"] > 0
    with pytest.raises(NotFoundError):
        suite.backtesting.run(strategy_id="missing", from_ts="a", to_ts="b")


def test_signals_and_performance():
    suite = crypto_enterprise.strategy_engine
    strategy = suite.builder.from_template(template="momentum", name="Mom", symbol="ETHUSDT")
    entry = suite.signals.entry(
        strategy_id=strategy["strategy_id"],
        symbol="ETHUSDT",
        side="long",
        price=3500,
        confidence=0.8,
    )
    assert entry["quality"] == "high"
    suite.signals.take_profit(strategy_id=strategy["strategy_id"], symbol="ETHUSDT", targets=[3600, 3700])
    with pytest.raises(ValidationError):
        suite.signals.entry(
            strategy_id=strategy["strategy_id"],
            symbol="ETHUSDT",
            side="sideways",
            price=1,
        )


def test_ai_strategy_and_bootstrap():
    suite = crypto_enterprise.strategy_engine
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.8.0-enterprise"
    assert boot["strategy_id"] and boot["backtest_id"] and boot["entry_id"]
    eval_row = suite.ai.evaluate(strategy_id=boot["strategy_id"], score=85)
    assert eval_row["grade"] == "A"
    for dtype in ("strategy", "backtesting", "signal", "performance", "ai_strategy"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype
    alloc = suite.portfolio_sim.allocate(name="Book", allocations={"BTC": 60, "ETH": 40})
    assert alloc["allocation_id"]


@pytest.mark.asyncio
async def test_api_strategy_engine(client):
    health = await client.get(f"{SE}/health")
    body = await health.json()
    assert body["application_version"] == "4.8.0-enterprise"
    assert body["strategy_builder_ready"] is True
    assert body["portfolio_simulation_ready"] is True

    boot = await client.post(f"{SE}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    signal = await client.post(
        f"{SE}/signals",
        json={
            "action": "entry",
            "strategy_id": boot_body["strategy_id"],
            "symbol": "BTCUSDT",
            "side": "long",
            "price": 69000,
            "confidence": 0.7,
        },
    )
    assert signal.status == 201

    ai = await client.post(
        f"{SE}/ai",
        json={"action": "evaluate", "strategy_id": boot_body["strategy_id"], "score": 70},
    )
    assert ai.status == 201

    for path in (PREFIX, TA, MM, MI):
        resp = await client.get(f"{path}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.8.0-enterprise"


def test_docs_and_regression_16_4():
    for name in (
        "STRATEGY_ENGINE.md",
        "BACKTESTING_ENGINE.md",
        "SIGNAL_GENERATION.md",
        "PERFORMANCE_ANALYTICS.md",
        "AI_STRATEGY_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_STRATEGY_ENGINE.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "strategy_engine" / "facade.py").exists()

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
    assert (ROOT / "applications" / "crypto_enterprise" / "market_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "market_microstructure" / "facade.py").exists()
