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
        "id": str(uuid.uuid4()),
        "request_number": "AUTO-9999",
        "request_type": "AUTO_SEARCH",
        "manager_id": str(uuid.uuid4()),
        "manager_name": "Boroda_0003",
        "manager_telegram_id": 393792086,
    }
