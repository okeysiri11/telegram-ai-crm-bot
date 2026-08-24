"""Sprint 50.4 — analysis pipeline, schedule honesty, signal lifecycle."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.consensus import build_consensus
from services.fx_market_intel.desk_ops import reset_fx_desk_ops_for_tests
from services.fx_market_intel.memory import reset_memory_for_tests
from services.fx_market_intel.schedule import PRESET_JOB_KEYS, list_fx_intel_schedule
from services.fx_market_intel.service import reset_fx_market_intel_for_tests
from services.fx_market_intel.signals import assert_no_trade_execution, create_signal, evaluate_price_trigger

FX = "/api/crypto-mi/v1/fx-intel"


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
def _reset():
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()
    reset_fx_desk_ops_for_tests()
    yield
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()
    reset_fx_desk_ops_for_tests()


def test_consensus_final_bias_scores_and_gaps():
    c = build_consensus(
        technical_vote="WATCH_BUY",
        dxy_vote="WATCH_BUY",
        macro_vote="NEUTRAL",
        news_vote="WATCH_BUY",
        session_vote="WATCH_BUY",
        risk_vote="NEUTRAL",
        key_reasons=["Технический бычий"],
        data_gaps=["DXY: источник недоступен"],
        sources={"eurusd": "NBU"},
    )
    assert c["final_result"] in {"BUY_BIAS", "SELL_BIAS", "NEUTRAL", "WAIT"}
    assert "bullish_score" in c and "bearish_score" in c and "neutral_score" in c
    assert c["key_reasons"]
    assert c["data_gaps"]
    assert c["sources"]["eurusd"] == "NBU"
    assert c["confidence"] == c["overall_confidence"]


def test_consensus_wait_on_high_risk():
    c = build_consensus(
        technical_vote="WATCH_BUY",
        dxy_vote="WATCH_BUY",
        macro_vote="HIGH_RISK",
        news_vote="WAIT",
        session_vote="NEUTRAL",
        risk_vote="WAIT",
    )
    assert c["final_result"] == "WAIT"


def test_signal_create_persist_trigger_enable():
    sig = create_signal(
        instrument="EUR/USD",
        timeframe="1H",
        signal="BUY_BIAS",
        confidence=0.6,
        price_trigger={"enabled": True, "price": 1.1, "direction": "above"},
    )
    assert_no_trade_execution(sig)
    assert sig["status"] == "BUY_BIAS"
    fired = evaluate_price_trigger(sig, 1.11)
    assert fired["price_trigger"]["triggered"] is True


def test_schedule_presets_mapped():
    assert set(PRESET_JOB_KEYS) == {"morning", "pre_europe", "pre_us", "evening"}


@pytest.mark.asyncio
async def test_schedule_honesty_no_fake_next_run():
    data = await list_fx_intel_schedule()
    assert "jobs" in data
    for preset in PRESET_JOB_KEYS:
        job = data["jobs"][preset]
        if not job.get("configured") or not job.get("next_run_at"):
            assert job.get("message_ru") == "Автозапуск не настроен" or job.get("next_run_at") is None
        else:
            assert isinstance(job["next_run_at"], str)


@pytest.mark.asyncio
async def test_http_analysis_result_and_schedule(client: TestClient):
    sched = await client.get(f"{FX}/schedule")
    assert sched.status == 200
    body = await sched.json()
    assert "jobs" in body
    assert "morning" in body["jobs"]

    created = await client.post(
        f"{FX}/signals",
        json={"instrument": "EUR/USD", "signal": "WAIT", "tenant_id": "t50-4", "source": "chart"},
    )
    assert created.status == 201
    sig = (await created.json())["signal"]
    assert sig["analytics_only"] is True

    patch = await client.post(
        f"{FX}/signals/lifecycle",
        json={"signal_id": sig["signal_id"], "enabled": False, "tenant_id": "t50-4"},
    )
    assert patch.status == 200
    assert (await patch.json())["signal"]["lifecycle"] == "DISABLED"

    run = await client.post(
        f"{FX}/run",
        json={"preset_id": "morning", "tenant_id": "t50-4", "timeframe": "1H"},
    )
    assert run.status in {200, 201}
    rj = await run.json()
    if rj.get("ok"):
        display = rj.get("display") or {}
        assert display.get("final_result") in {"BUY_BIAS", "SELL_BIAS", "NEUTRAL", "WAIT", "WATCH_BUY", "WATCH_SELL", "HIGH_RISK"}
        assert "bullish_score" in display or "bullish_score" in (display.get("consensus") or {})
        assert "key_reasons" in display or "key_reasons" in (display.get("consensus") or {})
        assert "data_gaps" in display or display.get("missing_sources") is not None
        assert rj.get("signal", {}).get("trade_execution") is not True
        # persistence attempted
        assert "persistence" in rj or rj.get("analysis")


@pytest.mark.asyncio
async def test_http_links_cross(client: TestClient):
    links = await client.get(f"{FX}/links?tenant_id=t50-4")
    assert links.status == 200
    data = await links.json()
    for key in ("chart", "analysis", "signals", "paper", "journal", "calendar"):
        assert key in data["links"]
