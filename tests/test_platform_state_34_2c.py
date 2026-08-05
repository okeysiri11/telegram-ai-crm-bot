"""Sprint 34.2C — Unified Platform State, Sync Engine, Cross-Client Runtime."""

from __future__ import annotations

import pytest

from platform_state.clients import (
    ai_runtime,
    desktop_runtime,
    mobile_runtime,
    telegram_runtime,
    web_runtime,
)
from platform_state.conflict import conflict_resolver
from platform_state.memory_store import memory_adapter
from platform_state.models import ALL_SLICES, EntityMeta
from platform_state.service import platform_state
from platform_state.sync_engine import sync_engine


@pytest.fixture(autouse=True)
def _reset_platform_state():
    platform_state.reset()
    yield
    platform_state.reset()


def test_status_and_snapshot_slices():
    status = platform_state.status()
    assert status["sprint"] in {"34.2C", "34.2D"}
    assert status["unified_platform_state"] is True
    assert status["event_bus"] == "events.event_bus.PlatformEventBus"
    snap = platform_state.snapshot(user_id="u1", telegram_id=42, workspace_id="crm")
    assert set(snap.slices.keys()) == set(ALL_SLICES)
    assert snap.user_id == "u1"
    data = snap.to_dict()
    assert data["sprint"] in {"34.2C", "34.2D"}
    assert "tasks" in data["slices"]
    assert "conversations" in data["slices"]
    assert "memory" in data["slices"]


@pytest.mark.asyncio
async def test_telegram_to_web_task_sync():
    received: list[str] = []

    async def on_web(event):
        received.append(event.entity_id)

    sync_engine.subscribe_client("web_test", on_web)
    task = await telegram_runtime.create_task(
        title="Follow up lead",
        creator_telegram_id=1001,
        actor_id="tg:1001",
    )
    assert task["task_id"]
    assert received == [task["task_id"]]
    delta = web_runtime.delta(None, slices=["tasks"])
    assert delta["count"] >= 1
    assert any(e["entity_id"] == task["task_id"] for e in delta["events"])


@pytest.mark.asyncio
async def test_web_to_telegram_notification_sync():
    note = await web_runtime.notify(
        title="Deal closed",
        body="Acme signed",
        user_id="u-web",
        telegram_id=55,
    )
    delta = telegram_runtime.delta(None, slices=["notifications"])
    assert any(e["entity_id"] == note["notification_id"] for e in delta["events"])
    snap = platform_state.snapshot(user_id="u-web", slices=["notifications"])
    notifs = snap.slices["notifications"].data["notifications"]
    assert any(n["notification_id"] == note["notification_id"] for n in notifs)


@pytest.mark.asyncio
async def test_desktop_to_telegram_calendar_sync():
    ev = await desktop_runtime.create_calendar_event(
        title="Standup",
        start_time="2026-08-03T09:00:00Z",
        creator_telegram_id=77,
    )
    delta = telegram_runtime.delta(None, slices=["calendar"])
    assert any(e["entity_id"] == ev["event_id"] for e in delta["events"])


@pytest.mark.asyncio
async def test_mobile_to_web_crm_sync():
    lead = await mobile_runtime.upsert_lead({"name": "Jane", "stage": "new"})
    delta = web_runtime.delta(None, slices=["crm"])
    assert any(e["entity_id"] == lead["id"] for e in delta["events"])
    snap = platform_state.snapshot(slices=["crm"])
    assert any(l["id"] == lead["id"] for l in snap.slices["crm"].data["leads"])


@pytest.mark.asyncio
async def test_conversation_shared_across_clients():
    tg_conv = await telegram_runtime.ensure_conversation(
        "tg-chat-9",
        user_id="u1",
        telegram_id=9,
        workspace_id="crm",
    )
    cid = tg_conv["conversation_id"]
    await telegram_runtime.append_message(cid, "Hello from Telegram")
    await web_runtime.ensure_conversation("web-thread-9", user_id="u1", telegram_id=9)
    await ai_runtime.append_message(cid, "AI continues", role="assistant")
    await desktop_runtime.append_message(cid, "Desktop reply")
    conv = platform_state.snapshot(user_id="u1", slices=["conversations"])
    rows = conv.slices["conversations"].data["conversations"]
    match = next(c for c in rows if c["conversation_id"] == cid)
    texts = [m["content"] for m in match["messages"]]
    assert "Hello from Telegram" in texts
    assert "AI continues" in texts
    assert "Desktop reply" in texts
    assert match["client_bindings"].get("telegram") == "tg-chat-9"


@pytest.mark.asyncio
async def test_memory_shared_user_workspace_conversation():
    tg_conv = await telegram_runtime.ensure_conversation("mem-1", user_id="u-mem", telegram_id=1)
    cid = tg_conv["conversation_id"]
    await ai_runtime.store_memory(
        scope="user",
        scope_id="u-mem",
        content="Prefers concise answers",
        conversation_id=cid,
    )
    await web_runtime.store_memory(
        scope="workspace",
        scope_id="crm",
        content="Q3 pipeline focus",
    )
    await telegram_runtime.store_memory(
        scope="conversation",
        scope_id=cid,
        content="Discussing Acme deal",
        conversation_id=cid,
    )
    mem = platform_state.snapshot(user_id="u-mem", workspace_id="crm", slices=["memory"])
    records = mem.slices["memory"].data["records"]
    contents = {r["content"] for r in records}
    assert "Prefers concise answers" in contents
    assert "Q3 pipeline focus" in contents
    conv = platform_state.snapshot(user_id="u-mem", slices=["conversations"])
    row = next(c for c in conv.slices["conversations"].data["conversations"] if c["conversation_id"] == cid)
    assert len(row["memory_refs"]) >= 1


@pytest.mark.asyncio
async def test_file_upload_appears_in_conversation_and_files():
    conv = await telegram_runtime.ensure_conversation("file-chat", user_id="u-f")
    cid = conv["conversation_id"]
    f = await telegram_runtime.upload_file("contract.pdf", conversation_id=cid, mime="application/pdf")
    await web_runtime.append_message(
        cid,
        "See attachment",
        attachments=[{"file_id": f["file_id"], "name": "contract.pdf"}],
    )
    snap = platform_state.snapshot(user_id="u-f", slices=["files", "documents", "conversations"])
    assert any(x["file_id"] == f["file_id"] for x in snap.slices["files"].data["files"])
    assert any(x["file_id"] == f["file_id"] for x in snap.slices["documents"].data["documents"])


@pytest.mark.asyncio
async def test_offline_delta_only():
    cursor = desktop_runtime.register_cursor()
    rev = cursor["last_revision"]
    await web_runtime.create_task(title="A", creator_telegram_id=1)
    await mobile_runtime.notify(title="N", body="b", user_id="u")
    delta = desktop_runtime.delta(rev)
    assert delta["count"] >= 2
    head = delta["revision"]
    empty = desktop_runtime.delta(head)
    assert empty["count"] == 0


def test_conflict_resolver_stale_rejected():
    server = EntityMeta(entity_type="task", entity_id="1", version=3)
    result = conflict_resolver.resolve(
        server=server,
        incoming_version=2,
        incoming_payload={"v": 2},
        server_payload={"v": 3},
    )
    assert result.resolved is False
    assert result.strategy == "reject_stale"
    ok = conflict_resolver.resolve(
        server=server,
        incoming_version=4,
        incoming_payload={"v": 4},
        server_payload={"v": 3},
    )
    assert ok.resolved is True


@pytest.mark.asyncio
async def test_workspace_sync():
    data = web_runtime.snapshot(slices=["workspaces"])
    assert "workspaces" in data["slices"]
    changed = await platform_state.workspaces.change(
        "crm",
        source_client="web",
        actor_id="owner",
        changes={"active": True},
    )
    assert changed["workspace_id"] == "crm"
    delta = mobile_runtime.delta(None, slices=["workspaces"])
    assert any(e["entity_type"] == "workspace" for e in delta["events"])


@pytest.mark.asyncio
async def test_ai_and_telegram_share_memory_store():
    await ai_runtime.store_memory(scope="user", scope_id="shared", content="one memory")
    await telegram_runtime.store_memory(scope="user", scope_id="shared", content="same scope")
    both = memory_adapter.list_scope("user", "shared")
    assert len(both) == 2


@pytest.mark.asyncio
async def test_task_complete_sync():
    task = await telegram_runtime.create_task(title="Done soon", creator_telegram_id=3)
    done = await platform_state.tasks.complete(
        task_id=task["task_id"],
        user_telegram_id=3,
        source_client="web",
        skip_db=True,
    )
    assert done["status"] == "DONE"
    delta = platform_state.delta(None, slices=["tasks"])
    assert any(e["action"] in {"created", "updated"} for e in delta["events"])
