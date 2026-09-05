"""Sprint Recruiting 1.8 — real-provider connections foundation."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.campaign_model import normalize_campaign
from services.recruiting_ops.lead_ingest import find_provider_duplicate, merge_duplicate, normalize_provider_lead
from services.recruiting_ops.provider_adapters import get_adapter
from services.recruiting_ops.provider_contract import UNSUPPORTED, adapter_result
from services.recruiting_ops.secret_store import get_secret_store, redact_mapping
from services.recruiting_ops.tracking_lifecycle import WAITING_PROVIDER, classify_lifecycle

OPS = "/api/recruiting-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("RECRUITING_ALLOW_MOCK_PROVIDERS", "1")
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str = "ados") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": "platform_owner"}


def test_adapter_unsupported_is_typed():
    adapter = get_adapter("meta", mode="LIVE")
    result = adapter.invoke("send_message")
    assert result["ok"] is False
    assert result["unsupported"] is True
    assert result["error"] == UNSUPPORTED


def test_live_adapter_without_credentials_is_not_configured():
    result = get_adapter("google", mode="LIVE").health_check()
    assert result["connected"] is False
    assert result["status"] == "NOT_CONFIGURED"
    assert result["mode"] == "LIVE"


def test_mock_adapter_connects_visibly():
    adapter = get_adapter("tiktok", mode="MOCK")
    connected = adapter.connect()
    assert connected["mode"] == "MOCK"
    assert connected["connected"] is True
    assert connected["mock"] is True
    health = adapter.health_check()
    assert health["status"] == "CONNECTED"
    assert health["mode"] == "MOCK"


def test_secret_store_redacts_and_rotates():
    store = get_secret_store()
    meta = store.put("meta", "access_token", "super-secret-token")
    assert meta["present"] is True
    assert meta.get("value") is None
    assert store.get("meta", "access_token") == "super-secret-token"
    rotated = store.rotate("meta", "access_token", "new-token")
    assert rotated["rotated_at"]
    public = redact_mapping({"access_token": "new-token", "account": "act_1"})
    assert public["access_token"] is True
    assert "new-token" not in str(public)


def test_campaign_lifecycle_statuses():
    item = normalize_campaign({"name": "Launch", "status": "draft", "provider": "meta"})
    assert item["status"] == "DRAFT"
    assert item["sync_state"] == "NOT_SYNCED"
    paused = normalize_campaign({"status": "paused"}, existing=item)
    assert paused["status"] == "PAUSED"


def test_lead_normalize_and_dedup_preserves_history():
    first = normalize_provider_lead(
        {
            "name": "Анна",
            "email": "anna@example.com",
            "provider": "meta",
            "external_id": "m-1",
            "utm_source": "meta",
            "utm_campaign": "one",
        }
    )
    second = normalize_provider_lead(
        {
            "name": "Анна",
            "email": "anna@example.com",
            "provider": "meta",
            "external_id": "m-1",
            "utm_source": "google",
            "utm_campaign": "two",
        }
    )
    existing = {**first, "id": "lead-1", "notes": "history"}
    found = find_provider_duplicate([existing], second)
    assert found is existing
    patch = merge_duplicate(existing, second)
    assert patch["last_touch_source"] == "google"
    assert "notes" not in patch


def test_attribution_chain():
    from services.recruiting_ops.attribution import attribution_chain

    chain = attribution_chain({"provider": "meta", "status": "qualified", "id": "l1", "first_touch_source": "meta"})
    assert chain["provider"] == "meta"
    assert chain["qualified"] is True
    assert chain["first_touch"]["source"] == "meta"
    assert chain["multi_touch_ready"] is True


def test_automation_defaults_to_approval():
    from services.recruiting_ops.automation import evaluate_rule, normalize_rule

    parsed = normalize_rule({"rule_type": "pause_if_cpl_exceeded", "threshold": 10})
    assert parsed["item"]["approval_required"] is True
    ev = evaluate_rule(parsed["item"], metrics={"cpl": 50, "leads": 1})
    assert ev["result"] == "APPROVAL_REQUIRED"
    assert ev["auto_applied"] is False


def test_ai_recommendation_is_advisory():
    from services.recruiting_ops.ai_optimization import AI_LIVE_WRITE_ACCESS, apply_human_decision, build_recommendation

    assert AI_LIVE_WRITE_ACCESS is False
    rec = build_recommendation({"recommendation": "decrease_budget", "reason": "CPL"})
    assert rec["item"]["advisory_only"] is True
    decided = apply_human_decision(rec["item"], "APPROVE")
    assert decided["item"]["live_applied"] is False


async def test_provider_center_not_configured(client: TestClient):
    org = f"pc-{uuid.uuid4().hex[:8]}"
    res = await client.get(f"{OPS}/providers", headers=_hdr(org))
    assert res.status == 200
    body = await res.json()
    by = {item["provider"]: item for item in body["items"]}
    for key in ("meta", "google", "tiktok", "telegram", "whatsapp", "email"):
        if key == "telegram":
            assert by[key]["status"] == "DISABLED"
            assert by[key]["frozen"] is True
            assert by[key]["connect_cta"] is False
            continue
        assert by[key]["status"] == "NOT_CONFIGURED"
        assert by[key]["connected"] is False
        assert by[key]["mode"] in {"LIVE", "MOCK"}


async def test_configure_redacts_secrets(client: TestClient):
    res = await client.post(
        f"{OPS}/providers/meta/configure",
        json={"ad_account_id": "act_1", "access_token": "secret-live-token"},
        headers=_hdr(f"cfg-{uuid.uuid4().hex[:8]}"),
    )
    assert res.status == 200
    item = (await res.json())["item"]
    assert item["status"] in {"CONFIGURING", "AUTHORIZING"}
    assert item["connected"] is False
    blob = str(await res.json()) if False else str(item)
    assert "secret-live-token" not in blob
    assert item["credential_presence"]["fields"]["access_token"]["present"] is True


async def test_mock_connect_reactivates_waiting_provider(client: TestClient, monkeypatch):
    org = f"prv-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("VANGUARD_ORGANIZATION_ID", org)
    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(org)
    event = {
        "id": str(uuid.uuid4()),
        "event_id": str(uuid.uuid4()),
        "delivery_status": WAITING_PROVIDER,
        "destination": "meta",
        "event_type": "page_view",
        "durable": True,
        "organization_id": org,
    }
    svc._bag(org)["tracking"].append(event)
    assert classify_lifecycle(event) == WAITING_PROVIDER
    res = await client.post(f"{OPS}/providers/meta/connect", json={"mode": "MOCK"}, headers=_hdr(org))
    assert res.status == 200
    body = await res.json()
    assert body["item"]["mode"] == "MOCK"
    assert body["item"]["status"] == "CONNECTED"
    assert body["reactivation"]["activated"] >= 1
    item = svc._find(org, "tracking", event["id"])
    assert item["delivery_status"] == "RETRYING"


async def test_provider_lead_ingest_dedup(client: TestClient):
    payload = {
        "name": "Борис",
        "email": f"b.{uuid.uuid4().hex[:6]}@example.com",
        "provider": "google",
        "external_id": f"g-{uuid.uuid4().hex[:8]}",
        "utm_source": "google",
        "utm_campaign": "hire",
    }
    first = await client.post(f"{OPS}/providers/leads", json=payload, headers=_hdr())
    assert first.status == 201
    second = await client.post(
        f"{OPS}/providers/leads",
        json={**payload, "utm_source": "tiktok", "notes_ignored": "x"},
        headers=_hdr(),
    )
    assert second.status == 200
    body = await second.json()
    assert body["duplicate"] is True
    assert body["item"]["last_touch_source"] == "tiktok"


async def test_ads_control_center_has_no_live_data(client: TestClient):
    res = await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=_hdr())
    body = await res.json()
    assert body["overview"]["no_live_data"] is True
    assert body["overview"]["spend"] is None
    assert "Нет живых данных" in str(body["overview"]["message_ru"])
    assert body["connected"] is False
    assert body["ai_optimization"]["live_write_access"] is False
    assert body["automation"]["approval_required_default"] is True


async def test_automation_and_ai_api(client: TestClient):
    created = await client.post(
        f"{OPS}/automation/rules",
        json={"rule_type": "notify_spend_without_leads"},
        headers=_hdr(),
    )
    assert created.status == 201
    rule = (await created.json())["item"]
    assert rule["approval_required"] is True
    ran = await client.post(
        f"{OPS}/automation/rules/{rule['id']}/run",
        json={"metrics": {"spend": 10, "leads": 0}},
        headers=_hdr(),
    )
    assert ran.status == 200
    assert (await ran.json())["evaluation"]["result"] == "APPROVAL_REQUIRED"
    rec = await client.post(
        f"{OPS}/ai/recommendations",
        json={"recommendation": "pause_campaign", "reason": "Нет лидов"},
        headers=_hdr(),
    )
    assert rec.status == 201
    rec_id = (await rec.json())["item"]["id"]
    decided = await client.post(
        f"{OPS}/ai/recommendations/{rec_id}/decision",
        json={"decision": "REJECT"},
        headers=_hdr(),
    )
    assert (await decided.json())["item"]["status"] == "REJECTED"
    assert (await decided.json())["item"]["live_applied"] is False


async def test_health_still_green_with_providers_not_configured(client: TestClient):
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] in {"recruiting_1.8", "recruiting_1.9", "recruiting_1.10", "recruiting_1.11", "recruiting_1.12"}
    assert health["tracking_health"]["code"] == "CONNECTED"
    diag = await (await client.get(f"{OPS}/ops/diagnostics", headers=_hdr())).json()
    assert diag["components"]["postgresql"]["code"] in {"CONNECTED", "DEGRADED", "NOT_CONFIGURED"}
    assert diag["provider_health"]["infra_independent"] is True
    assert diag["components"]["meta_ads"]["code"] == "NOT_CONFIGURED"


async def test_adapter_result_helper():
    payload = adapter_result(ok=False, error="X", message_ru="нет")
    assert payload["fake_data"] is False
    assert payload["ok"] is False
