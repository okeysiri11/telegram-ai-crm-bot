"""Tests — Technical Analysis / TradingView (Sprint 16.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.technical_analysis.analysis import INDICATORS, PATTERNS, STRUCTURES


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crypto-enterprise/v1"
TA = "/api/crypto-ta/v1"
PE = "/api/port-enterprise/v1"


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


def test_version_technical_analysis_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.7.1-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.0-enterprise"
    assert health["tradingview_integration_ready"] is True
    assert health["technical_analysis_ready"] is True
    assert health["pattern_recognition_ready"] is True
    assert health["ai_technical_intelligence_ready"] is True
    assert health["crypto_enterprise_foundation_ready"] is True


def test_tradingview_and_charts():
    suite = crypto_enterprise.technical_analysis
    tv = suite.tradingview.connect_api(account="qa")
    assert tv["connection_id"]
    wl = suite.tradingview.sync_watchlist(name="QA", symbols=["BTCUSDT"])
    assert wl["watchlist_id"]
    chart = suite.charts.create(symbol="BTCUSDT", chart_type="candlestick")
    assert chart["chart_id"]
    mtf = suite.charts.multi_timeframe(symbol="BTCUSDT", timeframes=["1h", "4h"])
    assert mtf["analysis_id"]


def test_indicators_and_patterns():
    suite = crypto_enterprise.technical_analysis
    for ind in INDICATORS:
        row = suite.indicators.compute(indicator=ind, symbol="ETHUSDT")
        assert row["indicator"] == ind
    for structure in STRUCTURES:
        assert suite.structures.detect(structure=structure, symbol="BTCUSDT")["structure"] == structure
    for pattern in PATTERNS:
        kwargs = {"pattern": pattern, "symbol": "BTCUSDT"}
        if pattern == "candlestick":
            kwargs["candle_pattern"] = "doji"
        assert suite.patterns.recognize(**kwargs)["pattern"] == pattern
    with pytest.raises(ValidationError):
        suite.indicators.compute(indicator="unknown", symbol="BTCUSDT")


def test_ai_analysis_and_bootstrap():
    suite = crypto_enterprise.technical_analysis
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.7.1-enterprise"
    assert boot["signal_id"] and boot["setup_id"]
    signal = suite.ai.signal_confidence(symbol="SOLUSDT", side="long", confidence=0.9)
    assert signal["confidence"] == 0.9
    for dtype in ("trading", "indicator", "pattern", "ai_analysis"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_technical_analysis(client):
    health = await client.get(f"{TA}/health")
    body = await health.json()
    assert body["application_version"] == "4.7.1-enterprise"
    assert body["tradingview_integration_ready"] is True
    assert body["technical_analysis_ready"] is True

    boot = await client.post(f"{TA}/bootstrap", json={})
    assert boot.status == 201

    ind = await client.post(
        f"{TA}/indicators",
        json={"indicator": "rsi", "symbol": "BTCUSDT", "timeframe": "1h"},
    )
    assert ind.status == 201

    pat = await client.post(
        f"{TA}/patterns",
        json={"pattern": "bull_flag", "symbol": "BTCUSDT", "timeframe": "4h"},
    )
    assert pat.status == 201

    ai = await client.post(
        f"{TA}/ai",
        json={"action": "signal", "symbol": "BTCUSDT", "side": "long", "confidence": 0.75},
    )
    assert ai.status == 201

    # Prior foundation routes still registered
    ce = await client.get(f"{PREFIX}/health")
    assert ce.status == 200
    ce_body = await ce.json()
    assert ce_body["application_version"] == "4.7.1-enterprise"


def test_docs_and_regression_16_1():
    for name in (
        "TRADINGVIEW_INTEGRATION.md",
        "TECHNICAL_ANALYSIS.md",
        "MARKET_INDICATORS.md",
        "PATTERN_RECOGNITION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_TECHNICAL_ANALYSIS.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "technical_analysis" / "facade.py").exists()

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
    assert "4.7.1-enterprise" in manifest
    assert "16.1" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "exchanges.py").exists()
    _ = PE
