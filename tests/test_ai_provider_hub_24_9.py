"""Tests — Enterprise AI Provider Hub & Model Router (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_ai_provider_hub.models import (
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    PROVIDER_KINDS,
    ROUTE_CRITERIA,
)


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
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
]
APH = "/api/enterprise-aph/v1"


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


def test_version_aph_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.3"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["ai_provider_hub_ready"] is True
    assert health["model_router_ready"] is True
    assert health["fallback_engine_ready"] is True
    assert health["ai_cost_control_ready"] is True
    assert health["engines"]["ai_provider_hub"] == "1.0"
    assert health["learning_engine_ready"] is True
    assert "openai" in PROVIDER_KINDS
    assert "local_corporate" in PROVIDER_KINDS
    assert "company_policy" in ROUTE_CRITERIA
    assert "learning_engine" in INTEGRATION_TARGETS
    assert KPI_TARGETS["provider_independence"] is True
    assert "no_direct_provider_calls" in PRINCIPLES


def test_router_fallback_security_invoke():
    suite = enterprise_hub.ai_provider_hub
    suite.register_provider(
        provider_id="prov_openai",
        name="OpenAI",
        kind="openai",
        endpoint="https://api.openai.com/v1",
        supported_models=["gpt-4o-mini"],
        cost_per_1k=0.15,
    )
    suite.register_provider(
        provider_id="prov_anthropic",
        name="Anthropic",
        kind="anthropic",
        endpoint="https://api.anthropic.com",
        supported_models=["claude-haiku"],
        cost_per_1k=0.25,
    )
    suite.register_provider(
        provider_id="local_corporate",
        name="Corp",
        kind="local_corporate",
        endpoint="http://localhost:8080/v1",
        supported_models=["corp-llm"],
        cost_per_1k=0.01,
    )
    suite.register_model(model_id="gpt-4o-mini", provider_id="prov_openai", quality_score=0.85, speed_score=0.9, cost_per_1k=0.15)
    suite.register_model(model_id="claude-haiku", provider_id="prov_anthropic", quality_score=0.88, speed_score=0.8, cost_per_1k=0.25)
    suite.register_model(model_id="corp-llm", provider_id="local_corporate", quality_score=0.7, speed_score=0.75, cost_per_1k=0.01)

    route = suite.route(task_type="general_chat", prefer_quality=True)
    assert route["via_hub_only"] is True
    assert route["direct_provider_call"] is False
    assert route["selected_model"] in ("gpt-4o-mini", "claude-haiku", "corp-llm")

    local_route = suite.route(task_type="secure_local", require_local=True)
    assert local_route["selected_provider"] == "local_corporate"

    fb = suite.fallback(
        chain=[
            {"provider_id": "prov_openai", "model_id": "gpt-4o-mini"},
            {"provider_id": "prov_anthropic", "model_id": "claude-haiku"},
            {"provider_id": "local_corporate", "model_id": "corp-llm"},
        ],
        fail_until=2,
    )
    assert fb["success"] is True
    assert fb["fallback_used"] is True
    assert fb["provider_id"] == "local_corporate"
    assert len(fb["journal"]) == 3

    fail_all = suite.fallback(chain=[{"provider_id": "a"}, {"provider_id": "b"}], fail_until=2)
    assert fail_all["error"] is True

    prompt = suite.assemble_prompt(template="enterprise_default", user_prompt="Hello", brand_dna={"tone": "clear"})
    assert prompt["single_entry_point"] is True

    costs = suite.track_cost(entries=[{"provider_id": "prov_openai", "client_id": "c1", "agent_id": "a1", "unit": "ops", "task_type": "chat", "cost": 0.05}])
    assert costs["total_cost"] == 0.05

    usage = suite.usage_analytics(requests=[{"success": True, "latency_ms": 50, "cost": 0.05, "quality": 0.9, "fallback_used": False, "model_id": "gpt-4o-mini"}])
    assert usage["request_count"] == 1

    with pytest.raises(ValidationError):
        suite.secure(secret_ref="sk-raw-key")

    sec = suite.secure(secret_ref="vault://providers/openai/api_key", allowed_models=["gpt-4o-mini"])
    assert sec["raw_key_exposed"] is False
    assert sec["keys_encrypted_at_rest"] is True

    inv = suite.invoke(task_type="general_chat", user_prompt="ping")
    assert inv["via_hub_only"] is True
    assert inv["direct_provider_call"] is False


def test_bootstrap_aph():
    suite = enterprise_hub.ai_provider_hub
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.3"
    assert boot["ai_provider_hub_ready"] is True
    assert boot["model_router_ready"] is True
    assert boot["fallback_engine_ready"] is True
    assert boot["ai_cost_control_ready"] is True
    assert boot["direct_provider_call"] is False
    assert boot["via_hub_only"] is True
    assert boot["provider_independence"] is True
    assert boot["supported_provider_kinds"] == len(PROVIDER_KINDS)
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["integrations"]["business_modules_call_hub_only"] is True


@pytest.mark.asyncio
async def test_api_aph(client):
    health = await client.get(f"{APH}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.3"
    assert body["ai_provider_hub_ready"] is True

    boot = await client.post(f"{APH}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["model_router_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.3"


def test_docs_and_regression_24_9():
    for name in (
        "ENTERPRISE_AI_PROVIDER_HUB.md",
        "APH_PROVIDERS_MODELS.md",
        "APH_ROUTER_FALLBACK.md",
        "APH_COST_SECURITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AI_PROVIDER_HUB.md").exists()
    assert (ROOT / "platform_enterprise_ai_provider_hub" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_provider_hub" / "facade.py").exists()

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
    assert '"application_version": "9.0.3"' in manifest
    assert "26.4" in manifest
