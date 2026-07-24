"""Tests — Enterprise Digital Twin 2.0 (Sprint 24.8 / v7.8.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_digital_twin.models import KPI_TARGETS, PRINCIPLES, SYNC_TARGETS, TIME_PRESETS


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
    "/api/enterprise-eco/v1",
    "/api/enterprise-cpl/v1",
    "/api/enterprise-eon/v1",
    "/api/enterprise-eoc/v1",
    "/api/enterprise-epr/v1",
    "/api/enterprise-eao/v1",
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
]
ETW = "/api/enterprise-etw/v1"


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


def test_version_etw_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.8.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.7.0"
    assert health["enterprise_digital_twin_ready"] is True
    assert health["live_state_ready"] is True
    assert health["twin_sync_ready"] is True
    assert health["twin_time_machine_ready"] is True
    assert health["engines"]["enterprise_digital_twin"] == "1.0"
    # legacy EDT remains
    assert health["digital_twin_ready"] is True
    assert "predictive_intelligence" in SYNC_TARGETS
    assert "1h" in TIME_PRESETS
    assert KPI_TARGETS["realtime_updates"] is True
    assert set(PRINCIPLES)


def test_twin_live_sync_dashboard():
    suite = enterprise_hub.enterprise_digital_twin
    twin = suite.create_twin(
        company_id="co_demo",
        branches=[{"branch_id": "b1", "name": "Main"}],
        employees=[{"employee_id": "e1", "team": "front", "branch_id": "b1"}],
        customers=[{"customer_id": "c1"}],
    )
    assert twin["version"] == "2.0"

    live = suite.live_state(
        company_id="co_demo",
        metrics={"customers": 5, "active_appointments": 2, "sales": 400, "staff_load": 0.6},
    )
    assert live["realtime"] is True
    assert live["metrics"]["customers"] == 5

    org = suite.organization_map(company_id="co_demo")
    assert org["visual"] is True
    assert any(n["type"] == "branch" for n in org["nodes"])

    procs = suite.processes(
        company_id="co_demo",
        processes=[
            {"id": "p1", "status": "running"},
            {"id": "p2", "status": "awaiting_approval"},
            {"id": "p3", "status": "error"},
        ],
    )
    assert len(procs["running"]) == 1
    assert len(procs["awaiting_approval"]) == 1

    sync = suite.sync_twin(company_id="co_demo")
    assert sync["all_ok"] is True
    assert sync["realtime"] is True

    tm = suite.time_machine(company_id="co_demo", preset="1h")
    assert tm["preset"] == "1h"

    impact = suite.change_impact(
        changed_objects=["sales"],
        affected_processes=["p1"],
        ai_consumers=["predictive_intelligence"],
        updated_forecasts=["revenue"],
    )
    assert "sales" in impact["changed_objects"]

    state = suite.twin_state(company_id="co_demo")
    assert state["api"] == "enterprise-etw"
    assert state["version"] == "2.0"
    assert "predictive_intelligence" in state["source_for"]

    dash = suite.owner_dashboard(company_id="co_demo")
    assert dash["single_monitoring_point"] is True
    assert dash["ai_may_act"] is False

    with pytest.raises(ValidationError):
        suite.time_machine(company_id="co_demo", preset="2y")


def test_bootstrap_etw():
    suite = enterprise_hub.enterprise_digital_twin
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.8.0"
    assert boot["enterprise_digital_twin_ready"] is True
    assert boot["realtime"] is True
    assert boot["all_synced"] is True
    assert boot["ai_may_act"] is False
    assert boot["source_for_pin_esl_eao"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_etw(client):
    health = await client.get(f"{ETW}/health")
    body = await health.json()
    assert body["application_version"] == "7.8.0"
    assert body["enterprise_digital_twin_ready"] is True

    boot = await client.post(f"{ETW}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["live_state_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.8.0"


def test_docs_and_regression_24_5():
    for name in (
        "ENTERPRISE_DIGITAL_TWIN_2.md",
        "ETW_REGISTRY_LIVE.md",
        "ETW_PROCESS_AI_TIME.md",
        "ETW_SYNC_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DIGITAL_TWIN_2.md").exists()
    assert (ROOT / "platform_enterprise_digital_twin" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "enterprise_digital_twin" / "facade.py").exists()

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
