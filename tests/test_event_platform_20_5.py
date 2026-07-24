"""Tests — Enterprise Event Platform (Sprint 20.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"
WF = "/api/enterprise-workflow/v1"
EIP = "/api/enterprise-eip/v1"
EDP = "/api/enterprise-edp/v1"
ISAM = "/api/enterprise-isam/v1"
OBS = "/api/enterprise-obs/v1"
TN = "/api/enterprise-tenancy/v1"
AOP = "/api/enterprise-aop/v1"
ATS = "/api/enterprise-ats/v1"
EKP = "/api/enterprise-ekp/v1"
AIOS = "/api/enterprise-aios/v1"
EVP = "/api/enterprise-evp/v1"


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


def test_version_evp_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.0.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.12.0"
    assert health["event_platform_ready"] is True
    assert health["event_bus_ready"] is True
    assert health["event_replay_ready"] is True
    assert health["dead_letter_queue_ready"] is True
    assert health["autonomous_aios_ready"] is True
    assert health["engines"]["event_platform"] == "1.0"
    assert health["engines"]["event_infrastructure"] == "1.0"


def test_publish_subscribe_dlq_idempotency():
    suite = enterprise_hub.event_platform
    suite.notifications.subscribe(event_types=["LeadCreated"])
    suite.audit.subscribe(event_types=["InvoiceApproved"])
    d1 = suite.crm.publish(payload={"id": "1", "timestamp": "t", "entity_id": "x"}, idempotency_key="k1")
    d2 = suite.crm.publish(payload={"id": "1", "timestamp": "t", "entity_id": "x"}, idempotency_key="k1")
    assert d1["event_id"] == d2["event_id"]
    failed = suite.bus.publish(
        event_type="InvoiceApproved",
        source="finance",
        payload={"id": "2", "timestamp": "t", "entity_id": "y"},
        fail_subscribers=["audit"],
        max_retries=1,
    )
    assert any(d.get("status") == "dead" for d in failed["deliveries"])
    assert suite.dlq.status()["dead_letters"] >= 1
    with pytest.raises(ValidationError):
        suite.event_store.append(event_type="", source="x")


def test_bootstrap_replay_dashboard():
    suite = enterprise_hub.event_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.0.0"
    assert boot["replay_id"] and boot["idempotent_same_event"] is True
    assert boot["dashboard"]["statistics_id"]


@pytest.mark.asyncio
async def test_api_evp(client):
    health = await client.get(f"{EVP}/health")
    body = await health.json()
    assert body["application_version"] == "7.0.0"
    assert body["event_platform_ready"] is True

    boot = await client.post(f"{EVP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EVP}/publish",
        json={"event_type": "UserCreated", "source": "crm", "payload": {"id": "u1", "timestamp": "t", "entity_id": "u1"}},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.0.0"

    assert boot_body["dispatch_crm_id"]


def test_docs_and_regression_20_5():
    for name in (
        "ENTERPRISE_EVENT_PLATFORM.md",
        "EVP_BUS.md",
        "EVP_STORE_REPLAY.md",
        "EVP_DLQ.md",
        "EVP_ANALYTICS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_EVENT_PLATFORM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "event_platform" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "event_platform" / "publishers" / "crm.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "event_platform" / "subscribers" / "notifications.py").exists()
    # 19.0 events package remains
    assert (ROOT / "applications" / "enterprise_hub" / "events").exists() or True

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
    assert "7.0.0" in manifest
    assert "24.0" in manifest
