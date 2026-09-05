"""Sprint Recruiting 3.3 Phase 2 — provider connection layer.

MOCKED HTTP is labelled. MOCKED PASS != LIVE CONNECTION PASS.
"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import quote

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.provider_adapters import get_adapter
from services.recruiting_ops.provider_http import set_http_transport
from services.recruiting_ops.provider_layer import (
    ADAPTER_METHODS,
    attribution_quality,
    fx_normalize,
    refuse_sync,
    resolve_spend,
    suggest_campaign_mapping,
)
from services.recruiting_ops.provider_oauth import decode_state, encode_state
from services.recruiting_ops.provider_state import CANONICAL_STATES, normalize_provider_status, public_connection_fields
from services.recruiting_ops.secret_store import get_secret_store, mask_secret

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"


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
def reset_ops():
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Recruiting-Organization-Id": org}


def _transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> dict:
    if "graph.facebook.com" in url and "/oauth/access_token" in url:
        return {"status": 200, "ok": True, "json": {"access_token": "injected-token", "expires_in": 3600}, "text": "{}"}
    if "graph.facebook.com" in url and "debug_token" in url:
        return {"status": 200, "ok": True, "json": {"data": {"scopes": ["ads_read"]}}, "text": "{}"}
    if "graph.facebook.com" in url and "/me/adaccounts" in url:
        return {"status": 200, "ok": True, "json": {"data": [{"id": "act_1", "name": "Acct", "currency": "EUR", "timezone_name": "Europe/Tallinn"}]}, "text": "{}"}
    if "graph.facebook.com" in url and "/me" in url:
        return {"status": 200, "ok": True, "json": {"id": "99", "name": "Meta User"}, "text": "{}"}
    if "graph.facebook.com" in url and "act_" in url:
        return {"status": 200, "ok": True, "json": {"id": "act_1", "name": "Acct", "account_status": 1, "currency": "EUR"}, "text": "{}"}
    if "oauth2.googleapis.com" in url:
        return {"status": 200, "ok": True, "json": {"access_token": "g-access", "refresh_token": "g-refresh", "expires_in": 3600, "scope": "https://www.googleapis.com/auth/adwords"}, "text": "{}"}
    if "customers:listAccessibleCustomers" in url:
        return {"status": 200, "ok": True, "json": {"resourceNames": ["customers/123"]}, "text": "{}"}
    if "googleads.googleapis.com" in url:
        return {"status": 200, "ok": True, "json": {"results": [{"customer": {"id": "123", "descriptiveName": "Cust"}}]}, "text": "{}"}
    if "tiktok.com" in url and "oauth2/access_token" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"access_token": "tt"}}, "text": "{}"}
    if "tiktok.com" in url and "advertiser/get" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"list": [{"advertiser_id": "tt1", "advertiser_name": "TT", "currency": "EUR"}]}}, "text": "{}"}
    if "tiktok.com" in url and "advertiser/info" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"list": [{"advertiser_id": "tt1", "name": "TT"}]}}, "text": "{}"}
    return {"status": 404, "ok": False, "json": {"error": "missing"}, "text": "missing"}


def test_canonical_state_machine():
    assert normalize_provider_status("CONFIGURING") == "AUTHORIZING"
    assert normalize_provider_status("ERROR") == "API_ERROR"
    assert set(CANONICAL_STATES) >= {"NOT_CONFIGURED", "CONNECTED", "DISCONNECTED"}
    fields = public_connection_fields({"provider": "meta", "status": "CONNECTED", "live_verified": False})
    assert fields["status"] == "AUTHORIZING"
    assert fields["connected"] is False


def test_spend_policy_does_not_stack():
    prefer = resolve_spend(manual=10, provider=4, policy="PREFER_PROVIDER", connected=True)
    assert prefer["amount"] == 4
    assert prefer["origin"] == "PROVIDER"
    assert prefer["stacked"] is False
    manual = resolve_spend(manual=10, provider=None, policy="PREFER_PROVIDER", connected=False)
    assert manual["amount"] == 10
    assert manual["origin"] == "MANUAL"


def test_fx_does_not_invent_rates():
    fx = fx_normalize(100, source_currency="USD", reporting_currency="EUR")
    assert fx["normalization_status"] == "UNAVAILABLE"
    assert fx["fx_rate_used"] is None
    assert fx["native_amount"] == 100


def test_mapping_ambiguous_is_conflict():
    suggestion = suggest_campaign_mapping(
        {"external_id": "x", "utm_campaign": "same"},
        [{"id": "a", "utm_campaign": "same"}, {"id": "b", "utm_campaign": "same"}],
    )
    assert suggestion["state"] == "CONFLICT"
    assert suggestion["ambiguous"] is True
    unique = suggest_campaign_mapping({"utm_campaign": "only"}, [{"id": "a", "utm_campaign": "only"}])
    assert unique["state"] == "SUGGESTED"
    assert attribution_quality(utm_campaign="only") == "UTM_MATCH"


def test_sync_refuses_without_credentials():
    blocked = refuse_sync("meta", configured=False, connected=False, account_selected=False)
    assert blocked["error"] == "NOT_CONFIGURED"
    assert blocked["fake_data"] is False


def test_adapter_contract_methods_exist():
    adapter = get_adapter("meta", mode="LIVE")
    for name in ADAPTER_METHODS:
        assert adapter.supports(name), name


def test_credential_masking():
    assert mask_secret("super-secret") == "••••"
    desc = get_secret_store().describe("meta", "access_token")
    assert desc["value"] is None


async def test_oauth_state_tamper_rejected():
    state = encode_state(provider="meta", organization_id="org-1")
    assert decode_state(state)["ok"] is True
    assert decode_state(state[:-3] + "zzz")["ok"] is False


async def test_oauth_callback_replay_rejected(client: TestClient, monkeypatch):
    monkeypatch.setenv("META_ADS_APP_ID", "app")
    monkeypatch.setenv("META_ADS_APP_SECRET", "secret")
    set_http_transport(_transport)
    org = f"p2r-{uuid.uuid4().hex[:8]}"
    state = encode_state(provider="meta", organization_id=org)
    first = await (await client.get(f"{OPS}/oauth/meta/callback?code=abc&state={quote(state, safe='')}&format=json")).json()
    assert first.get("ok") is True
    assert first.get("connected") is False
    assert first.get("item", {}).get("status") == "AUTHORIZING"
    assert "injected-token" not in str(first)
    second = await (await client.get(f"{OPS}/oauth/meta/callback?code=abc&state={quote(state, safe='')}&format=json")).json()
    assert second.get("ok") is False
    assert "уже использован" in str(second.get("message_ru") or "")


async def test_google_oauth_requires_developer_token(client: TestClient, monkeypatch):
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_SECRET", "csec")
    monkeypatch.delenv("GOOGLE_ADS_DEVELOPER_TOKEN", raising=False)
    body = await (await client.get(f"{OPS}/providers/google/oauth/start", headers=_hdr(f"p2g-{uuid.uuid4().hex[:8]}"))).json()
    assert body["ok"] is False
    assert body["error"] == "NOT_CONFIGURED"
    assert "developer token" in body["message_ru"].lower() or "DEVELOPER_TOKEN" in body["message_ru"]


async def test_missing_credentials_sync_not_configured(client: TestClient):
    org = f"p2s-{uuid.uuid4().hex[:8]}"
    body = await (await client.post(f"{OPS}/providers/meta/sync-metrics", json={}, headers=_hdr(org))).json()
    assert body["ok"] is False
    assert body["error"] == "NOT_CONFIGURED"
    assert body.get("fake_data") is False


async def test_observer_cannot_connect_provider(client: TestClient):
    org = f"p2o-{uuid.uuid4().hex[:8]}"
    denied = await (await client.get(f"{OPS}/providers/meta/oauth/start", headers=_hdr(org, "observer"))).json()
    assert denied.get("ok") is False
    assert denied.get("error") == "forbidden"
    view = await (await client.get(f"{OPS}/providers", headers=_hdr(org, "observer"))).json()
    assert view.get("ok") is True


async def test_recruiter_cannot_select_ads_account(client: TestClient):
    org = f"p2rec-{uuid.uuid4().hex[:8]}"
    denied = await (await client.post(f"{OPS}/providers/meta/select-account", json={"account_id": "act_1"}, headers=_hdr(org, "recruiter"))).json()
    assert denied.get("ok") is False
    assert denied.get("error") == "forbidden"


async def test_cross_tenant_credentials_isolated(client: TestClient):
    set_http_transport(_transport)
    a = f"p2a-{uuid.uuid4().hex[:8]}"
    b = f"p2b-{uuid.uuid4().hex[:8]}"
    get_secret_store().put("meta", "access_token", "tenant-a-secret-token", organization_id=a)
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr(b))).json()
    assert "tenant-a-secret-token" not in str(listed)
    diag = await (await client.get(f"{OPS}/providers/meta/diagnostics", headers=_hdr(b))).json()
    assert "tenant-a-secret-token" not in str(diag)
    assert diag.get("connected") is False


async def test_token_not_returned_or_logged(client: TestClient, caplog):
    caplog.set_level(logging.DEBUG)
    token = "super-secret-phase2-token"
    org = f"p2l-{uuid.uuid4().hex[:8]}"
    await client.post(f"{OPS}/providers/meta/configure", json={"ad_account_id": "act_1", "access_token": token}, headers=_hdr(org))
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json()
    diag = await (await client.get(f"{OPS}/providers/meta/diagnostics", headers=_hdr(org))).json()
    assert token not in str(listed)
    assert token not in str(diag)
    assert token not in caplog.text
    assert listed["items"][0]["status"] != "CONNECTED" or listed["items"][0].get("live_verified") is True


async def test_account_select_mocked_is_not_live(client: TestClient):
    set_http_transport(_transport)
    org = f"p2sel-{uuid.uuid4().hex[:8]}"
    get_secret_store().put("meta", "access_token", "injected", organization_id=org)
    selected = await (await client.post(f"{OPS}/providers/meta/select-account", json={"account_id": "act_1"}, headers=_hdr(org))).json()
    assert selected.get("mocked") is True
    assert selected.get("item", {}).get("live_verified") is False
    assert selected.get("item", {}).get("mocked_http") is True


async def test_disconnect_purges_tokens_keeps_history(client: TestClient):
    set_http_transport(_transport)
    org = f"p2d-{uuid.uuid4().hex[:8]}"
    store = get_secret_store()
    store.put("meta", "access_token", "to-purge", organization_id=org)
    await client.post(f"{OPS}/providers/meta/configure", json={"ad_account_id": "act_1"}, headers=_hdr(org))
    await client.post(f"{OPS}/campaigns", json={"name": "Keep", "project_key": "vanguard"}, headers=_hdr(org))
    gone = await (await client.post(f"{OPS}/providers/meta/disconnect", json={}, headers=_hdr(org))).json()
    assert gone.get("item", {}).get("status") == "DISCONNECTED"
    assert store.get("meta", "access_token", organization_id=org) is None
    campaigns = await (await client.get(f"{OPS}/campaigns", headers=_hdr(org))).json()
    assert any(item.get("name") == "Keep" for item in campaigns.get("items") or [])


async def test_permission_and_expired_token_states():
    from services.recruiting_ops.provider_state import status_from_error

    assert status_from_error("TOKEN_EXPIRED") == "TOKEN_EXPIRED"
    assert status_from_error("PERMISSION_ERROR") == "PERMISSION_ERROR"


async def test_diagnostics_safe_and_russian(client: TestClient):
    org = f"p2diag-{uuid.uuid4().hex[:8]}"
    body = await (await client.get(f"{OPS}/providers/google/diagnostics", headers=_hdr(org))).json()
    assert body.get("auth_configured") is False
    assert body.get("connected") is False
    assert body.get("secrets") is None
    assert "Google" in (body.get("message_ru") or "") or "GOOGLE" in (body.get("message_ru") or "")


async def test_mapping_confirm_and_conflict(client: TestClient):
    org = f"p2m-{uuid.uuid4().hex[:8]}"
    camp = (await (await client.post(f"{OPS}/campaigns", json={"name": "Internal", "project_key": "vanguard"}, headers=_hdr(org))).json())["item"]
    mapped = await (await client.post(f"{OPS}/providers/mappings", json={"provider": "meta", "external_campaign_id": "ext-1", "internal_campaign_id": camp["id"]}, headers=_hdr(org))).json()
    assert mapped["item"]["state"] == "MAPPED"
    other = (await (await client.post(f"{OPS}/campaigns", json={"name": "Other", "project_key": "vanguard"}, headers=_hdr(org))).json())["item"]
    conflict = await (await client.post(f"{OPS}/providers/mappings", json={"provider": "meta", "external_campaign_id": "ext-1", "internal_campaign_id": other["id"]}, headers=_hdr(org))).json()
    assert conflict.get("ok") is False
    assert conflict.get("state") == "CONFLICT"


async def test_unsigned_ingest_still_rejected(client: TestClient, monkeypatch):
    monkeypatch.setenv("VANGUARD_INGEST_REQUIRE_SIGNATURE", "1")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", "phase2-secret")
    res = await client.post(INGEST, data=b'{"email":"x@example.com"}', headers={"Content-Type": "application/json"})
    body = await res.json()
    assert res.status == 401
    assert body.get("error") == "missing_signature"


async def test_control_center_stays_not_configured(client: TestClient):
    org = f"p2cc-{uuid.uuid4().hex[:8]}"
    center = await (await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=_hdr(org))).json()
    assert all(card["connected"] is False for card in center["provider_connect"])
    assert all(card["status"] != "CONNECTED" for card in center["provider_connect"])
    assert center["spend_policy"]["stacked"] is False
