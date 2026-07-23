"""Tests — Enterprise Observability (Sprint 19.9)."""

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


def test_version_observability_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.4.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.4.5-enterprise"
    assert health["enterprise_observability_ready"] is True
    assert health["metrics_platform_ready"] is True
    assert health["distributed_tracing_ready"] is True
    assert health["incident_management_ready"] is True
    assert health["enterprise_isam_ready"] is True
    assert health["engines"]["observability"] == "1.0"


def test_metrics_logs_tracing_alerts():
    suite = enterprise_hub.observability
    svc = suite.services.register(name="qa-api", kind="microservice")
    suite.services.set_health(service_id=svc["service_id"], health_status="healthy")
    met = suite.metrics.record(kind="api", value=33.0)
    log = suite.logging.write(
        kind="application", message="qa ok", service="qa-api", correlation_id="corr-qa"
    )
    search = suite.logging.search(correlation_id="corr-qa")
    assert search["count"] >= 1
    trace = suite.tracing.start(name="qa", correlation_id="corr-qa")
    suite.tracing.span(trace_id=trace["trace_id"], service="qa-api", operation="handle", duration_ms=9)
    suite.tracing.finish(trace_id=trace["trace_id"])
    alert = suite.alerting.fire(title="qa warn", level="warning", channel="telegram")
    assert met["metric_id"] and log["log_id"] and alert["alert_id"]
    with pytest.raises(ValidationError):
        suite.metrics.record(kind="unknown", value=1)


def test_incidents_diagnostics_bootstrap():
    suite = enterprise_hub.observability
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.4.6-enterprise"
    assert boot["trace_id"] and boot["incident_id"] and boot["diagnostic_id"]
    diag = suite.diagnostics.analyze(subject="qa", error="timeout")
    assert "recommendations" in diag
    for dtype in ("platform", "infrastructure", "ai", "integrations", "business"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_observability(client):
    health = await client.get(f"{OBS}/health")
    body = await health.json()
    assert body["application_version"] == "5.4.6-enterprise"
    assert body["enterprise_observability_ready"] is True
    assert body["metrics_platform_ready"] is True

    boot = await client.post(f"{OBS}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{OBS}/metrics",
        json={"kind": "cpu", "value": 11.5},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.4.6-enterprise"

    assert boot_body["export_otel_id"]


def test_docs_and_regression_19_9():
    for name in (
        "ENTERPRISE_OBSERVABILITY.md",
        "OBS_METRICS.md",
        "OBS_LOGGING_TRACING.md",
        "OBS_ALERTING.md",
        "OBS_DASHBOARDS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_OBSERVABILITY.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "observability" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "observability" / "collectors" / "system.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "observability" / "exporters" / "prometheus.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "observability" / "dashboards" / "platform.py").exists()

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
    assert "5.4.6-enterprise" in manifest
    assert "20.6" in manifest
