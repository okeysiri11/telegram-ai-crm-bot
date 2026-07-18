"""Shared pytest fixtures for integration tests."""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

# Tests always use PostgreSQL policy; SQLite must not bootstrap.
os.environ.setdefault("POSTGRES_ONLY", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("REDIS_REQUIRED", "false")


@pytest.fixture
def client_user_id() -> int:
    return 900_001


@pytest.fixture
def manager_user_id() -> int:
    return 900_002


@pytest.fixture
def mock_message(client_user_id: int):
    msg = MagicMock()
    user = MagicMock()
    user.id = client_user_id
    user.username = "test_client"
    user.full_name = "Test Client"
    user.first_name = "Test"
    user.last_name = "Client"
    user.language_code = "ru"
    msg.from_user = user
    msg.text = ""
    msg.answer = AsyncMock()
    msg.bot = MagicMock()
    msg.bot.send_message = AsyncMock()
    msg.contact = None
    msg.photo = None
    return msg


@pytest.fixture
def mock_fsm_context():
    ctx = AsyncMock()
    store: dict = {}

    async def get_data():
        return dict(store)

    async def update_data(**kwargs):
        store.update(kwargs)

    async def set_state(state):
        ctx._state = state

    async def get_state():
        return getattr(ctx, "_state", None)

    async def clear():
        store.clear()
        ctx._state = None

    ctx.get_data = get_data
    ctx.update_data = update_data
    ctx.set_state = set_state
    ctx.get_state = get_state
    ctx.clear = clear
    ctx._store = store
    return ctx


@pytest.fixture
def sample_submit_result():
    return {
        "request_number": "AUTO-9999",
        "request_type": "AUTO_SEARCH",
        "manager_id": str(uuid.uuid4()),
        "manager_name": "Boroda_0003",
        "manager_telegram_id": 393792086,
    }


@pytest.fixture(autouse=True)
def _configure_management_iam(monkeypatch):
    monkeypatch.setenv("IAM_JWT_SECRET", "pytest-management-secret-key-32bytes-min")
    monkeypatch.setenv("IAM_LOGIN_SECRET", "pytest-login-secret")
    monkeypatch.setattr(
        "platform_identity.jwt_service.IAM_JWT_SECRET",
        "pytest-management-secret-key-32bytes-min",
        raising=False,
    )


@pytest.fixture
def auth_headers(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    from platform_identity.jwt_service import jwt_service
    from platform_identity.models import PlatformRole

    jwt_service.reset()
    tokens = jwt_service.issue_tokens(
        subject="telegram:42",
        roles=[PlatformRole.OWNER.value],
        permissions=[
            "management.read",
            "management.admin",
            "ai.read",
            "ai.use",
            "ai.admin",
            "plugins.read",
            "plugins.write",
            "integrations.read",
            "integrations.write",
            "jobs.read",
            "jobs.write",
            "observability.read",
            "observability.write",
        ],
        telegram_id=42,
    )
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def actor_header(auth_headers):
    """Backward-compatible alias — management API now requires JWT, not X-Actor-Telegram-Id."""
    return auth_headers


@pytest.fixture
def api_key_headers(monkeypatch):
    from platform_identity.api_keys import api_key_service

    api_key_service.reset()
    raw, _record = api_key_service.create_key(
        name="pytest-key",
        scopes=["management.read", "ai.read", "ai.use", "plugins.read"],
        telegram_id=42,
    )
    return {"X-API-Key": raw}


@pytest.fixture
def login_proof():
    return "pytest-login-secret"
