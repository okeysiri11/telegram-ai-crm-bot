"""Sprint 34.2D — Enterprise Runtime, Event Sourcing & Versioning Core."""

from __future__ import annotations

import pytest

from database.models.mixins import VersionMixin
from platform_state.clients import (
    ai_runtime,
    desktop_runtime,
    mobile_runtime,
    telegram_runtime,
    web_runtime,
)
from platform_state.conflict_engine import MergeStrategy, conflict_engine
from platform_state.entity import CanonicalEntity, ENTITY_TYPES
from platform_state.enterprise import enterprise_runtime
from platform_state.event_store import PlatformEventStore
from platform_state.models import EntityMeta
from platform_state.replay import replay_engine
from platform_state.service import platform_state
from platform_state.transaction import begin_transaction
from platform_state.version_engine import OptimisticLockError, version_engine


@pytest.fixture(autouse=True)
def _reset():
    platform_state.reset()
    yield
    platform_state.reset()


def test_version_mixin_td54_fields():
    assert hasattr(VersionMixin, "version")
    assert hasattr(VersionMixin, "change_id")
    assert hasattr(VersionMixin, "source_client")
    assert hasattr(VersionMixin, "workspace_id")
    # Sprint 35.1 — tenant scope stays on entity UUID tenant_id columns (no String collision).
    assert "tenant_id" not in VersionMixin.__dict__


def test_canonical_entity_mandatory_fields():
    ent = CanonicalEntity.create(
        entity_type="lead",
        data={"name": "Acme"},
        created_by="owner",
        workspace_id="crm",
        tenant_id="t1",
        source_client="web",
    )
    d = ent.to_dict()
    for key in (
        "id",
        "version",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "workspace_id",
        "tenant_id",
        "source_client",
        "change_id",
        "deleted_at",
        "metadata",
    ):
        assert key in d
    assert set(ENTITY_TYPES) >= {"user", "lead", "deal", "task", "conversation", "agent"}


def test_version_engine_history_compare_rollback():
    created = version_engine.create(
        entity_type="task",
        data={"title": "v1"},
        created_by="u1",
        source_client="web",
        workspace_id="ws",
    )
    v2 = version_engine.update(
        entity_type="task",
        entity_id=created.id,
        data={"title": "v2"},
        expected_version=1,
        updated_by="u1",
        source_client="telegram",
    )
    assert v2.version == 2
    hist = version_engine.history("task", created.id)
    assert len(hist) >= 2
    cmp = version_engine.compare("task", created.id, 1, 2)
    assert cmp["diff"]["title"]["old"] == "v1"
    assert cmp["diff"]["title"]["new"] == "v2"
    rolled = version_engine.rollback(
        entity_type="task",
        entity_id=created.id,
        to_version=1,
        updated_by="u1",
        source_client="web",
    )
    assert rolled.data["title"] == "v1"
    assert rolled.version >= 3


def test_optimistic_lock_reject():
    ent = version_engine.create(entity_type="deal", data={"amount": 1}, created_by="a")
    version_engine.update(entity_type="deal", entity_id=ent.id, data={"amount": 2}, expected_version=1)
    with pytest.raises(OptimisticLockError):
        version_engine.update(
            entity_type="deal",
            entity_id=ent.id,
            data={"amount": 3},
            expected_version=1,
        )


def test_event_store_durable_and_ordered():
    store = PlatformEventStore(memory=True)
    a = store.append(event_type="TaskCreated", entity_type="task", entity_id="1", payload={"n": 1})
    b = store.append(event_type="TaskUpdated", entity_type="task", entity_id="1", payload={"n": 2}, version=2)
    c = store.append(event_type="LeadCreated", entity_type="lead", entity_id="9", workspace_id="crm")
    assert a.seq < b.seq < c.seq
    stream = store.stream("task", "1")
    assert [e.event_type for e in stream] == ["TaskCreated", "TaskUpdated"]
    assert len(store.workspace_stream("crm")) == 1
    assert store.get(a.event_id) is not None


@pytest.mark.asyncio
async def test_web_telegram_desktop_mobile_ai_sync_matrix():
    task = await telegram_runtime.create_task(title="TG", creator_telegram_id=1)
    await web_runtime.notify(title="W", body="b", user_id="u")
    await desktop_runtime.create_calendar_event(
        title="D", start_time="2026-08-03T10:00:00Z", creator_telegram_id=1
    )
    lead = await mobile_runtime.upsert_lead({"name": "M"})
    await ai_runtime.store_memory(scope="user", scope_id="u", content="pref")
    await ai_runtime.upsert_lead({"name": "AI Lead", "source": "agent"})
    await platform_state.calendar.create_event(
        title="AI meet",
        start_time="2026-08-04T10:00:00Z",
        creator_telegram_id=1,
        source_client="ai",
        skip_db=True,
    )
    await platform_state.tasks.create(
        title="AI task",
        creator_telegram_id=1,
        source_client="ai",
        skip_db=True,
    )

    assert platform_state.events.count() >= 6
    delta = web_runtime.delta(None)
    ids = {e["entity_id"] for e in delta["events"]}
    assert task["task_id"] in ids
    assert lead["id"] in ids


@pytest.mark.asyncio
async def test_replay_rebuilds_state():
    ent = version_engine.create(
        entity_type="lead",
        data={"name": "ReplayMe"},
        created_by="u",
        source_client="web",
        workspace_id="crm",
    )
    version_engine.update(
        entity_type="lead",
        entity_id=ent.id,
        data={"name": "ReplayMe2"},
        expected_version=1,
        updated_by="u",
        source_client="telegram",
    )
    version_engine.reset()
    assert version_engine.get("lead", ent.id) is None
    result = replay_engine.replay_entity("lead", ent.id)
    assert result.applied >= 1
    head = version_engine.get("lead", ent.id)
    assert head is not None
    assert head.data["name"] == "ReplayMe2"


@pytest.mark.asyncio
async def test_workspace_and_time_travel_replay():
    a = version_engine.create(
        entity_type="task",
        data={"t": 1},
        workspace_id="ws-a",
        created_by="u",
        source_client="web",
    )
    version_engine.create(
        entity_type="task",
        data={"t": 2},
        workspace_id="ws-b",
        created_by="u",
        source_client="web",
    )
    version_engine.reset()
    ws = replay_engine.replay_workspace("ws-a")
    assert any(a.id in x for x in ws.entity_ids)
    head = version_engine.get("task", a.id)
    assert head is not None


def test_conflict_strategies():
    server = EntityMeta(entity_type="task", entity_id="1", version=3, updated_at="2026-01-01T00:00:00+00:00")
    server_payload = {"title": "server", "priority": "HIGH"}
    incoming = {"title": "client", "priority": "LOW", "note": "x"}

    reject = conflict_engine.resolve(
        server=server,
        incoming_version=2,
        incoming_payload=incoming,
        server_payload=server_payload,
        strategy=MergeStrategy.VERSION_REJECT,
    )
    assert reject.resolved is False

    lww = conflict_engine.resolve(
        server=server,
        incoming_version=3,
        incoming_payload=incoming,
        server_payload=server_payload,
        incoming_updated_at="2026-02-01T00:00:00+00:00",
        strategy=MergeStrategy.LAST_WRITE_WINS,
        incoming_source="telegram",
    )
    assert lww.resolved is True
    assert lww.winner["title"] == "client"

    merged = conflict_engine.resolve(
        server=server,
        incoming_version=3,
        incoming_payload=incoming,
        server_payload=server_payload,
        incoming_updated_at="2026-01-01T00:00:00+00:00",
        strategy=MergeStrategy.FIELD_MERGE,
        incoming_source="web",
    )
    assert merged.resolved is True
    assert merged.winner.get("note") == "x"

    manual = conflict_engine.resolve(
        server=server,
        incoming_version=2,
        incoming_payload=incoming,
        server_payload=server_payload,
        strategy=MergeStrategy.MANUAL_REVIEW,
        incoming_source="desktop",
    )
    assert manual.requires_manual_review is True
    assert conflict_engine.pending_reviews()

    def rule(server_p, incoming_p, _ctx):
        return {**server_p, "title": incoming_p["title"], "priority": server_p["priority"]}

    conflict_engine.register_business_rule("task", rule)
    biz = conflict_engine.resolve(
        server=server,
        incoming_version=2,
        incoming_payload=incoming,
        server_payload=server_payload,
        strategy=MergeStrategy.BUSINESS_RULE,
        entity_type="task",
    )
    assert biz.resolved is True
    assert biz.winner["priority"] == "HIGH"
    assert biz.winner["title"] == "client"


@pytest.mark.asyncio
async def test_audit_timeline_who_when_what():
    ent = version_engine.create(
        entity_type="notification",
        data={"body": "hi"},
        created_by="owner",
        source_client="web",
        workspace_id="ws",
        tenant_id="ten",
    )
    version_engine.update(
        entity_type="notification",
        entity_id=ent.id,
        data={"body": "hi2"},
        expected_version=1,
        updated_by="manager",
        source_client="telegram",
        agent_id="agent_owner",
    )
    timeline = platform_state.timeline.for_entity("notification", ent.id)
    assert len(timeline) >= 2
    last = timeline[-1]
    assert last.get("who") in {"manager", "owner"} or last.get("source_client")
    assert last.get("when") or last.get("occurred_at")
    assert last.get("old_value") is not None or last.get("new_value") is not None


@pytest.mark.asyncio
async def test_platform_transaction_commit_and_rollback():
    box: dict[str, list] = {"items": []}

    async def add_ok():
        box["items"].append("crm")
        return "crm"

    async def undo_ok():
        box["items"].remove("crm")

    async def add_task():
        box["items"].append("task")
        return "task"

    async def fail():
        raise RuntimeError("boom")

    tx = begin_transaction(source_client="web", actor_id="u")
    tx.add("crm", add_ok, undo=undo_ok).add("task", add_task).add("fail", fail)
    result = await tx.commit()
    assert result["status"] == "rolled_back"
    assert "crm" not in box["items"]

    box["items"].clear()
    tx2 = begin_transaction()
    tx2.add("a", add_ok).add("b", add_task)
    ok = await tx2.commit()
    assert ok["status"] == "committed"
    assert box["items"] == ["crm", "task"]


@pytest.mark.asyncio
async def test_offline_recovery_and_self_healing():
    cursor = desktop_runtime.register_cursor()
    await web_runtime.create_task(title="offline", creator_telegram_id=1)
    healed = platform_state.healing.on_reconnect(
        "desktop-1",
        last_revision=cursor["last_revision"],
        client_kind="desktop",
    )
    assert healed["healed"] is True
    assert len(healed["events"]) >= 1
    restart = platform_state.healing.on_worker_restart()
    assert restart["healed"] is True


@pytest.mark.asyncio
async def test_concurrent_editing_and_large_dataset():
    ent = version_engine.create(entity_type="lead", data={"n": 0}, created_by="a")

    async def bump(client: str, expected: int):
        return version_engine.update(
            entity_type="lead",
            entity_id=ent.id,
            data={"n": expected + 1, "by": client},
            expected_version=expected,
            source_client=client,
            updated_by=client,
        )

    await bump("web", 1)
    with pytest.raises(OptimisticLockError):
        await bump("telegram", 1)

    store_count_before = platform_state.events.count()
    for i in range(50):
        await mobile_runtime.upsert_lead({"name": f"L{i}", "i": i})
    assert platform_state.events.count() >= store_count_before + 50
    events = platform_state.events.since_seq(0, limit=10_000)
    seqs = [e.seq for e in events]
    assert seqs == sorted(seqs)


@pytest.mark.asyncio
async def test_telemetry_and_enterprise_status():
    await telegram_runtime.create_task(title="metric", creator_telegram_id=1)
    snap = platform_state.telemetry.snapshot()
    assert snap["counters"]["events_total"] >= 1
    assert "events_per_sec" in snap
    status = enterprise_runtime.status()
    assert status["sprint"] == "34.2D"
    assert status["deterministic"] is True
    assert platform_state.status()["enterprise_runtime"] is True


@pytest.mark.asyncio
async def test_batch_and_cache():
    result = await enterprise_runtime.batch(
        [
            {"op": "task.create", "title": "b1", "telegram_id": 1, "skip_db": True},
            {"op": "notification.create", "title": "n", "body": "x", "user_id": "u"},
        ]
    )
    assert result["count"] == 2
    enterprise_runtime.cache.put_entity("task", "x", {"ok": True})
    assert enterprise_runtime.cache.get_entity("task", "x") == {"ok": True}
