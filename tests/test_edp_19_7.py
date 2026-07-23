"""Tests — Enterprise Data Platform & MDM (Sprint 19.7)."""

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


def test_version_edp_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.4.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.4.4-enterprise"
    assert health["enterprise_data_platform_ready"] is True
    assert health["master_data_ready"] is True
    assert health["data_quality_ready"] is True
    assert health["data_governance_ready"] is True
    assert health["enterprise_integration_platform_ready"] is True
    assert health["engines"]["edp"] == "1.0"


def test_master_quality_governance():
    suite = enterprise_hub.edp
    a = suite.manager.create_master(entity_type="company", name="QA Co")
    b = suite.manager.create_master(entity_type="user", name="QA User")
    rel = suite.master.relate(
        from_entity_id=b["entity_id"],
        to_entity_id=a["entity_id"],
        relation="works_for",
    )
    suite.master.upsert(entity_type="company", name="QA Co", source="dup")
    qual = suite.quality.run(entity_type="company")
    assert qual["score"] <= 1.0
    pol = suite.governance.set_policy(entity_id=a["entity_id"], classification="internal")
    assert rel["relationship_id"] and pol["policy_id"]
    with pytest.raises(ValidationError):
        suite.manager.create_master(entity_type="company", name="")


def test_lineage_versioning_ai_bootstrap():
    suite = enterprise_hub.edp
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.4.5-enterprise"
    assert boot["customer_id"] and boot["quality_id"] and boot["rollback_id"]
    ai = suite.ai.assist(action="detect_anomalies", subject="financial_object")
    assert ai["assist_id"]
    for dtype in ("quality", "catalog", "governance", "lineage", "analytics"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_edp(client):
    health = await client.get(f"{EDP}/health")
    body = await health.json()
    assert body["application_version"] == "5.4.5-enterprise"
    assert body["enterprise_data_platform_ready"] is True
    assert body["master_data_ready"] is True

    boot = await client.post(f"{EDP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EDP}/master",
        json={"entity_type": "product", "name": "API Product"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.4.5-enterprise"

    assert boot_body["schema_user_id"]


def test_docs_and_regression_19_7():
    for name in (
        "ENTERPRISE_DATA_PLATFORM.md",
        "MASTER_DATA.md",
        "DATA_QUALITY.md",
        "DATA_GOVERNANCE.md",
        "DATA_LINEAGE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DATA_PLATFORM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_platform" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_platform" / "entities" / "companies.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_platform" / "validation" / "duplicate_detector.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_platform" / "analytics" / "quality_dashboard.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "5.4.5-enterprise" in manifest
    assert "20.5" in manifest
