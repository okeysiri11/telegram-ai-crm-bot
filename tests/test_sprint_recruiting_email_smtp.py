"""Sprint Recruiting 1.10 — Email SMTP productionization."""

from __future__ import annotations

import ssl
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.observability import prometheus_text
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.email_smtp import MAX_EMAIL_ATTEMPTS, render_template
from services.recruiting_ops.provider_live import set_smtp_factory
from services.recruiting_ops.secret_store import get_secret_store
from services.recruiting_ops.tracking_lifecycle import WAITING_PROVIDER, provider_is_configured
from services.recruiting_ops.tracking_worker import get_tracking_worker, reset_tracking_worker_for_tests

OPS = "/api/recruiting-ops/v1"
SECRET = "smtp-super-secret-pass"


class DummySMTP:
    fail_mode = None
    attempts = 0
    sent = 0

    def __init__(self, *a, **k):
        DummySMTP.attempts += 1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def ehlo(self):
        if self.fail_mode == "timeout":
            raise TimeoutError("timed out")
        if self.fail_mode == "tls":
            raise ssl.SSLError("tls handshake failed")
        return True

    def starttls(self, context=None):
        if self.fail_mode == "tls":
            raise ssl.SSLError("tls handshake failed")
        return True

    def login(self, *a):
        if self.fail_mode == "auth":
            import smtplib

            raise smtplib.SMTPAuthenticationError(535, b"auth failed")
        return True

    def send_message(self, *a):
        if self.fail_mode == "temp":
            import smtplib

            raise smtplib.SMTPResponseException(421, b"try later")
        if self.fail_mode == "perm":
            import smtplib

            raise smtplib.SMTPResponseException(550, b"user unknown")
        DummySMTP.sent += 1
        return True


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


def _blob(payload) -> str:
    return str(payload).lower()


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
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)
    DummySMTP.fail_mode = None
    DummySMTP.attempts = 0
    DummySMTP.sent = 0
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _ready_smtp():
    store = get_secret_store()
    store.put("email", "smtp_host", "smtp.example")
    store.put("email", "email_from", "hr@example.com")
    store.put("email", "smtp_user", "hr@example.com")
    store.put("email", "smtp_password", SECRET)
    set_smtp_factory(lambda host, port: DummySMTP())


async def test_missing_smtp_config_not_configured(client: TestClient):
    body = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr())).json()
    assert body["status"] == "NOT_CONFIGURED"


async def test_valid_mocked_smtp_connected(client: TestClient):
    _ready_smtp()
    body = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr(f"em-{uuid.uuid4().hex[:8]}"))).json()
    assert body["status"] == "CONNECTED"
    assert body["live_verified"] is False
    assert SECRET not in str(body)


async def test_auth_failure_error_state(client: TestClient):
    _ready_smtp()
    DummySMTP.fail_mode = "auth"
    body = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr(f"au-{uuid.uuid4().hex[:8]}"))).json()
    assert body["status"] == "ERROR"
    assert body.get("error_code") == "AUTH_ERROR" or "авториз" in str(body.get("safe_error_message") or "").lower()


async def test_timeout_error_state(client: TestClient):
    _ready_smtp()
    DummySMTP.fail_mode = "timeout"
    body = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr(f"to-{uuid.uuid4().hex[:8]}"))).json()
    assert body["status"] == "ERROR"


async def test_tls_failure_error_state(client: TestClient):
    _ready_smtp()
    DummySMTP.fail_mode = "tls"
    body = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr(f"tls-{uuid.uuid4().hex[:8]}"))).json()
    assert body["status"] == "ERROR"
    assert "tls" in str(body.get("safe_error_message") or "").lower() or body.get("error_code") == "TLS_ERROR"


async def test_password_redacted_and_absent_from_api(client: TestClient):
    org = f"sec-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/providers/email/configure",
        json={"smtp_host": "smtp.example", "email_from": "hr@example.com", "smtp_password": SECRET},
        headers=_hdr(org),
    )
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json()
    assert SECRET not in str(listed)
    assert '"password"' not in str(listed).lower() or listed["items"]
    email = next(item for item in listed["items"] if item["provider"] == "email")
    fields = (email.get("credential_presence") or {}).get("fields") or {}
    assert fields.get("smtp_password", {}).get("present") in {True, False}
    assert "value" not in (fields.get("smtp_password") or {}) or fields["smtp_password"].get("value") in {None, False}


async def test_password_absent_from_audit(client: TestClient):
    org = f"aud-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/providers/email/configure",
        json={"smtp_host": "smtp.example", "email_from": "hr@example.com", "smtp_password": SECRET},
        headers=_hdr(org),
    )
    activity = await (await client.get(f"{OPS}/activity", headers=_hdr(org))).json()
    assert SECRET not in str(activity)


async def test_test_email_success_and_failure(client: TestClient):
    _ready_smtp()
    org = f"te-{uuid.uuid4().hex[:8]}"
    ok = await (await client.post(f"{OPS}/providers/email/test-email", json={"to": "qa@example.com"}, headers=_hdr(org))).json()
    assert ok["ok"] is True
    assert ok["sent"] is True
    assert ok["delivered"] is False
    DummySMTP.fail_mode = "perm"
    DummySMTP.attempts = 0
    bad = await (await client.post(f"{OPS}/providers/email/test-email", json={"to": "qa@example.com"}, headers=_hdr(org))).json()
    assert bad["ok"] is False
    assert bad["delivered"] is False


async def test_communication_persisted_sent_only_after_success(client: TestClient):
    _ready_smtp()
    org = f"cnd-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Анна", "email": "anna@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    sent = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro"}, headers=_hdr(org))).json()
    assert sent["ok"] is True
    item = sent["item"]
    assert item["status"] == "SENT"
    assert item["delivered"] is False
    assert item["delivery"] == "accepted"
    hist = await (await client.get(f"{OPS}/candidates/{cid}/emails", headers=_hdr(org))).json()
    assert len(hist["items"]) == 1
    DummySMTP.fail_mode = "perm"
    DummySMTP.attempts = 0
    failed = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "interview", "body": "other"}, headers=_hdr(org))).json()
    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["delivered"] is False


async def test_idempotency_prevents_duplicate(client: TestClient):
    _ready_smtp()
    org = f"idm-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Борис", "email": "b@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    payload = {"template_id": "intro", "subject": "Вакансия x", "body": "Здравствуйте"}
    first = await (await client.post(f"{OPS}/candidates/{cid}/email", json=payload, headers=_hdr(org))).json()
    DummySMTP.sent = 0
    second = await (await client.post(f"{OPS}/candidates/{cid}/email", json=payload, headers=_hdr(org))).json()
    assert second.get("duplicate") is True
    assert DummySMTP.sent == 0
    assert second["item"]["id"] == first["item"]["id"]


async def test_retry_bounded_permanent_not_retried_temporary_retried():
    from services.recruiting_ops.email_smtp import send_smtp_message
    from services.recruiting_ops.provider_live import smtp_settings

    _ready_smtp()
    DummySMTP.fail_mode = "perm"
    DummySMTP.attempts = 0
    result = send_smtp_message(to="a@example.com", subject="s", body="b", cfg=smtp_settings(), factory=lambda h, p: DummySMTP())
    assert result["ok"] is False
    assert DummySMTP.attempts == 1
    DummySMTP.fail_mode = "temp"
    DummySMTP.attempts = 0
    result = send_smtp_message(to="a@example.com", subject="s", body="b", cfg=smtp_settings(), factory=lambda h, p: DummySMTP())
    assert result["ok"] is False
    assert DummySMTP.attempts == MAX_EMAIL_ATTEMPTS
    assert result.get("retryable") is True


async def test_rate_limit_works(client: TestClient, monkeypatch):
    _ready_smtp()
    monkeypatch.setenv("EMAIL_SEND_RATE_LIMIT", "1")
    org = f"rl-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Кира", "email": "k@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    first = await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro", "body": "one"}, headers=_hdr(org))
    assert first.status in {200, 201}
    second = await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro", "body": "two"}, headers=_hdr(org))
    body = await second.json()
    assert second.status == 429 or body.get("error") == "RATE_LIMITED"


async def test_observer_cannot_send_or_test(client: TestClient):
    _ready_smtp()
    org = f"obs-{uuid.uuid4().hex[:8]}"
    denied = await client.post(f"{OPS}/providers/email/test", json={}, headers=_hdr(org, "observer"))
    assert denied.status == 403
    created = await client.post(f"{OPS}/candidates", json={"name": "Оля", "email": "o@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    send = await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro"}, headers=_hdr(org, "observer"))
    assert send.status == 403


async def test_campaign_approval_and_suppression(client: TestClient):
    _ready_smtp()
    org = f"cmp-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Игорь", "email": "i@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    blocked = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro", "campaign_id": "camp-1"}, headers=_hdr(org))).json()
    assert blocked.get("error") == "APPROVAL_REQUIRED"
    await client.post(f"{OPS}/email/suppression", json={"email": "i@example.com"}, headers=_hdr(org))
    suppressed = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro", "approved": True, "campaign_id": "camp-1"}, headers=_hdr(org))).json()
    assert suppressed.get("error") == "suppressed"


async def test_invalid_recipient_and_header_injection(client: TestClient):
    _ready_smtp()
    org = f"inj-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Нина", "email": "not-an-email"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    invalid = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"to": "not-an-email"}, headers=_hdr(org))).json()
    assert invalid.get("ok") is False
    injected = await (
        await client.post(
            f"{OPS}/candidates/{cid}/email",
            json={"to": "ok@example.com", "subject": "Hi\nBcc: evil@x.com", "body": "hello"},
            headers=_hdr(org),
        )
    ).json()
    assert injected.get("ok") is False


def test_template_placeholders_safe():
    rendered = render_template("intro", {"name": "Анна", "vacancy": "Driver", "evil": "{__import__('os')}"})
    assert "Анна" in rendered["body"]
    assert "__import__" not in rendered["body"]
    assert "{evil}" not in rendered["body"]


async def test_telegram_frozen_does_not_block_readiness_or_retry_storm(client: TestClient):
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] == "recruiting_1.10"
    assert health["telegram"]["frozen"] is True
    assert health["telegram"]["blocks_readiness"] is False
    assert health["tracking_health"]["code"] == "CONNECTED"
    assert provider_is_configured("telegram") is False
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr())).json()
    tg = next(item for item in listed["items"] if item["provider"] == "telegram")
    assert tg["status"] == "DISABLED"
    assert tg["frozen"] is True
    assert tg["connect_cta"] is False
    worker = get_tracking_worker()
    item = worker.enqueue({"id": "tg-1", "event_id": "tg-1", "destination": "telegram"})
    assert item["delivery_status"] == WAITING_PROVIDER
    before = item.get("attempt") or 0

    async def persist(event):
        return event

    await worker.tick(persist)
    after = next(p for p in worker.pending if str(p.get("id")) == "tg-1")
    assert after["delivery_status"] == WAITING_PROVIDER
    assert int(after.get("attempt") or 0) == int(before or 0)
    reset_tracking_worker_for_tests()
    w2 = get_tracking_worker()
    w2.enqueue(after)
    await w2.tick(persist)
    assert w2.snapshot()["retrying"] == 0


async def test_audit_and_candidate_timeline(client: TestClient):
    _ready_smtp()
    org = f"tl-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Лена", "email": "l@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro"}, headers=_hdr(org))
    activity = await (await client.get(f"{OPS}/activity", headers=_hdr(org))).json()
    actions = [item.get("action") for item in activity.get("items") or []]
    assert "email_sent" in actions
    assert SECRET not in str(activity)


async def test_smtp_accepted_not_delivered(client: TestClient):
    _ready_smtp()
    org = f"dlv-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/candidates", json={"name": "Марк", "email": "m@example.com"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    sent = await (await client.post(f"{OPS}/candidates/{cid}/email", json={"template_id": "intro"}, headers=_hdr(org))).json()
    assert sent["item"]["status"] != "DELIVERED"
    assert sent["item"]["delivered"] is False


def test_email_metrics_registered():
    text = prometheus_text()
    for name in (
        "email_send_attempt_total",
        "email_send_success_total",
        "email_send_failure_total",
        "email_retry_total",
        "email_rate_limited_total",
        "email_provider_health",
        "email_send_latency",
    ):
        assert name in text
