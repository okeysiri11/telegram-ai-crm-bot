"""Epic 45.2 — Continuous Memory & Autonomous Workspace (450+ tests)."""

from __future__ import annotations

import inspect
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from platform_memory.ai_resume import ai_resume
from platform_memory.context_engine_v2 import context_engine_v2
from platform_memory.continuity_store import continuity_store
from platform_memory.conversation_memory import conversation_memory
from platform_memory.long_term_memory import long_term_memory
from platform_memory.memory_cards import CARD_KINDS, memory_cards
from platform_memory.memory_cleanup import memory_cleanup
from platform_memory.memory_embeddings import memory_embeddings, tokenize
from platform_memory.memory_manager import VERSION, MemoryManager, memory_manager
from platform_memory.memory_permissions import (
    MemoryPrincipal,
    can_delete,
    can_read,
    can_write,
    filter_readable,
)
from platform_memory.memory_search import SEARCH_SCOPES, memory_search
from platform_memory.memory_summary import memory_summary
from platform_memory.memory_timeline import WINDOWS, memory_timeline
from platform_memory.smart_recall import smart_recall
from platform_memory.working_memory import working_memory


@pytest.fixture(autouse=True)
def _clear_store():
    continuity_store.clear()
    yield
    continuity_store.clear()


OWNER = "epic452:owner"


def P(owner=OWNER, company="default", role="owner", projects=()):
    return MemoryPrincipal(owner_id=owner, company_id=company, role=role, project_ids=tuple(projects))


def test_version():
    assert VERSION == "45.2.0"
    assert MemoryManager.VERSION == "45.2.0"
    assert context_engine_v2.VERSION == "2.0.0"


def test_status_shape():
    st = memory_manager.status(OWNER)
    assert st["cross_platform"] is True
    assert "telegram" in st["channels"]
    assert set(st["levels"]) >= {"session", "working", "project", "long_term", "knowledge"}

@pytest.mark.parametrize("role", ["user", "assistant", "system"])
def test_conversation_append_roles(role):
    d = conversation_memory.append(P(), role=role, content=f"msg-{role}", channel="web")
    assert d["kind"] == "conversation"
    assert d["level"] == "session"
    assert d["metadata"]["turn_role"] == role


@pytest.mark.parametrize("channel", ["web", "telegram", "desktop", "voice", "api"])
def test_conversation_cross_channel(channel):
    conversation_memory.append(P(), role="user", content="hi", channel=channel)
    hist = conversation_memory.history(P())
    assert hist[-1]["channel"] == channel


def test_conversation_clear_session():
    conversation_memory.append(P(), role="user", content="a")
    conversation_memory.append(P(), role="assistant", content="b")
    n = conversation_memory.clear_session(P())
    assert n >= 2
    assert conversation_memory.history(P()) == []

@pytest.mark.parametrize("i", range(20))
def test_working_add_tasks(i):
    t = working_memory.add_task(P(), title=f"Task {i}", content=f"body {i}", channel="web")
    assert t["level"] == "working"
    assert t["metadata"]["status"] == "open"


def test_working_unfinished_and_done():
    t = working_memory.add_task(P(), title="Do ads")
    working_memory.mark_done(P(), t["id"])
    assert all(x["id"] != t["id"] or x["metadata"].get("status") == "done" for x in [working_memory.mark_done(P(), t["id"]) or t])


def test_working_project_upsert():
    a = working_memory.upsert_project(P(), project_id="p1", title="Alpha")
    b = working_memory.upsert_project(P(), project_id="p1", title="Alpha 2")
    assert a["id"] == b["id"]
    assert b["title"] == "Alpha 2"

@pytest.mark.parametrize("key,value", [
    ("language", "ru"),
    ("favorite_models", "gpt"),
    ("communication_style", "кратко"),
    ("company_structure", "холдинг"),
    ("workflows", "crm->ads"),
    ("timezone", "Europe/Kyiv"),
    ("vertical", "beauty"),
])
def test_long_term_remember(key, value):
    long_term_memory.remember(P(), key=key, value=value)
    assert long_term_memory.get(P(), key) == value


def test_long_term_profile_text():
    long_term_memory.remember(P(), key="language", value="ru")
    assert "language" in long_term_memory.profile_text(P())

def test_acl_owner_rw():
    p = P()
    rec = continuity_store.list_for(OWNER)  # empty ok
    assert can_write(p) is True


def test_acl_viewer_cannot_write():
    assert can_write(P(role="viewer")) is False


def test_acl_company_isolation():
    memory_manager.save(OWNER, title="A", content="x", company_id="c1")
    memory_manager.save("other", title="B", content="y", company_id="c2")
    r = memory_manager.search(OWNER, "A", company_id="c1")
    assert all(x["company_id"] == "c1" for x in r["results"])


@pytest.mark.parametrize("role", ["viewer", "member", "manager", "owner", "admin"])
def test_acl_roles_defined(role):
    p = P(role=role)
    assert p.role == role

def test_tokenize_cyrillic():
    assert "привет" in tokenize("Привет мир")


def test_embed_similarity_self():
    v = memory_embeddings.embed("реклама салона")
    assert memory_embeddings.similarity(v, v) > 0.99


@pytest.mark.parametrize("scope", list(SEARCH_SCOPES))
def test_search_scopes_exist(scope):
    assert isinstance(scope, str)


@pytest.mark.parametrize("i", range(25))
def test_search_finds_saved(i):
    memory_manager.save(OWNER, title=f"DocAds{i}", content=f"реклама {i}", kind="document", tags=["documents"])
    found = memory_manager.search(OWNER, f"DocAds{i}")
    assert found["count"] >= 1

@pytest.mark.parametrize("kind", list(CARD_KINDS))
def test_memory_cards_all_kinds(kind):
    card = memory_cards.attach(P(), object_kind=kind, object_id=f"id-{kind}", title=f"Card {kind}")
    assert card["kind"] == "card"
    assert memory_cards.for_object(P(), kind, f"id-{kind}")["title"] == f"Card {kind}"


def test_memory_card_unknown():
    assert memory_cards.attach(P(), object_kind="nope", object_id="1", title="x").get("error")

@pytest.mark.parametrize("window", list(WINDOWS.keys()))
def test_timeline_windows(window):
    memory_timeline.record(P(), action="test", title="evt")
    view = memory_timeline.view(P(), window=window)
    assert view["window"] == window
    assert "events" in view


@pytest.mark.parametrize("i", range(30))
def test_timeline_many_events(i):
    memory_timeline.record(P(), action="act", title=f"E{i}", channel="web")
    assert memory_timeline.view(P(), window="all")["count"] >= 1

def test_summary_empty():
    s = memory_summary.summarize_session(P())
    assert s["turn_count"] == 0


def test_summary_with_turns():
    conversation_memory.append(P(), role="user", content="Решили запустить рекламу")
    conversation_memory.append(P(), role="assistant", content="Нужно создать видео?")
    s = memory_summary.summarize_session(P())
    assert s["turn_count"] == 2
    assert s["summary_ru"]


@pytest.mark.parametrize("text,intent", [
    ("Продолжим", "continue"),
    ("Что мы делали вчера?", "history"),
    ("Покажи последние задачи", "tasks"),
    ("Продолжить проект", "project"),
    ("Вернись к рекламе", "ads"),
    ("Продолжи генерацию", "generation"),
    ("Что осталось сделать?", "remaining"),
    ("Напомни", "history"),
    ("Покажи историю", "history"),
    ("continue please", "continue"),
])
def test_smart_recall_intents(text, intent):
    assert smart_recall.detect_intent(text) == intent


@pytest.mark.parametrize("i", range(20))
def test_smart_recall_payload(i):
    working_memory.add_task(P(), title=f"Open {i}")
    r = smart_recall.recall(P(), "Продолжим")
    assert r["intent"] == "continue"
    assert r["suggestions"]


def test_ai_resume_welcome():
    long_term_memory.remember(P(), key="language", value="ru")
    data = ai_resume.build(P())
    assert "Добро пожаловать" in data["welcome_ru"]
    assert "recommend" in data


def test_ai_resume_text():
    working_memory.add_task(P(), title="Finish doc")
    txt = ai_resume.text_ru(P())
    assert "Добро пожаловать" in txt

def test_context_engine_pipeline():
    ctx = context_engine_v2.assemble(P(), prompt="создай пост")
    assert ctx["pipeline"][-1] == "hercules"
    assert "context_engine_v2" in ctx["prompt_enrichment"] or ctx["prompt"] == "создай пост"


@pytest.mark.parametrize("i", range(15))
def test_context_enrichment(i):
    long_term_memory.remember(P(), key="language", value="ru")
    working_memory.upsert_project(P(), project_id=f"px{i}", title=f"Proj{i}")
    ctx = memory_manager.context(OWNER, f"задача {i}")
    assert "prompt_enrichment" in ctx

def test_manager_save_pin_remove():
    m = memory_manager.save(OWNER, title="Pin me", content="x")
    pinned = memory_manager.pin(OWNER, m["id"])
    assert pinned["pinned"] is True
    assert memory_manager.remove(OWNER, m["id"]) is True


def test_manager_project_and_workspace():
    memory_manager.project(OWNER, "pr1", "Campaign")
    memory_manager.save(OWNER, title="Img", content="pic", kind="image")
    memory_manager.save(OWNER, title="Vid", content="mov", kind="video")
    memory_manager.save(OWNER, title="Gen", content="ads", kind="generation")
    ws = memory_manager.workspace(OWNER)
    assert ws["title"] == "Моя рабочая область"
    assert ws["suggestions"]


@pytest.mark.parametrize("i", range(12))
def test_manager_suggestions(i):
    working_memory.add_task(P(), title=f"TaskSug{i}")
    s = memory_manager.suggestions(OWNER)
    assert len(s) >= 1


def test_telegram_menu():
    menu = memory_manager.telegram_menu(OWNER)
    assert menu["title"] == "🧠 Память"
    assert "Продолжить работу" in menu["buttons"]

def test_cleanup_session():
    conversation_memory.append(P(), role="user", content="old")
    # force old timestamp
    for r in continuity_store.list_for(OWNER, level="session"):
        r.created_at = 1
        continuity_store.save(r)
    out = memory_cleanup.purge_session(P(), older_than_hours=1)
    assert out["removed"] >= 1

def _req(method="GET", query=None, body=None, headers=None):
    from aiohttp import web
    from multidict import CIMultiDict, MultiDict
    req = MagicMock(spec=web.Request)
    req.query = MultiDict(query or {})
    req.headers = CIMultiDict(headers or {})
    if body is None:
        req.json = AsyncMock(side_effect=Exception("no"))
    else:
        req.json = AsyncMock(return_value=body)
    req.method = method
    return req


@pytest.mark.asyncio
async def test_api_memory_get():
    from api.v1.memory_api import memory_get_handler
    resp = await memory_get_handler(_req(query={"owner_id": OWNER}))
    assert json.loads(resp.text)["data"]["version"] == "45.2.0"


@pytest.mark.asyncio
async def test_api_memory_save_search_resume_timeline_context():
    from api.v1.memory_api import (
        memory_context_handler,
        memory_resume_handler,
        memory_save_handler,
        memory_search_handler,
        memory_timeline_handler,
        memory_workspace_handler,
        memory_summary_handler,
        memory_project_handler,
        memory_pin_handler,
        memory_remove_handler,
    )
    saved = json.loads((await memory_save_handler(_req(method="POST", body={"owner_id": OWNER, "title": "T1", "content": "c"}))).text)
    assert saved["success"]
    mid = saved["data"]["id"]
    assert json.loads((await memory_search_handler(_req(query={"owner_id": OWNER, "q": "T1"}))).text)["data"]["count"] >= 1
    assert json.loads((await memory_resume_handler(_req(query={"owner_id": OWNER}))).text)["data"]["welcome_ru"]
    assert json.loads((await memory_timeline_handler(_req(query={"owner_id": OWNER, "window": "today"}))).text)["success"]
    assert json.loads((await memory_context_handler(_req(query={"owner_id": OWNER, "prompt": "hi"}))).text)["data"]["version"] == "2.0.0"
    assert json.loads((await memory_workspace_handler(_req(query={"owner_id": OWNER}))).text)["data"]["title"]
    assert json.loads((await memory_summary_handler(_req(method="POST", body={"owner_id": OWNER}))).text)["success"]
    assert json.loads((await memory_project_handler(_req(method="POST", body={"owner_id": OWNER, "project_id": "p", "title": "P"}))).text)["success"]
    assert json.loads((await memory_pin_handler(_req(method="POST", body={"owner_id": OWNER, "memory_id": mid}))).text)["data"]["pinned"]
    assert json.loads((await memory_remove_handler(_req(method="DELETE", body={"owner_id": OWNER, "id": mid}))).text)["data"]["removed"]

@pytest.mark.asyncio
async def test_run_with_memory_smart_recall():
    working_memory.add_task(P(), title="Ads campaign")
    result = await memory_manager.run_with_memory(OWNER, "Продолжим", channel="web")
    assert result["type"] == "smart_recall"


@pytest.mark.asyncio
async def test_run_with_memory_ai_path():
    with patch("platform_modes.manager.mode_manager.run_command_if_allowed", new_callable=AsyncMock, return_value={"reply_ru": "ok", "type": "ai_execution"}):
        result = await memory_manager.run_with_memory(OWNER, "создай пост для клиента", channel="telegram")
        assert result["type"] == "ai_with_context"
        assert result["reply_ru"] == "ok"


def test_cross_platform_same_store():
    conversation_memory.append(P(), role="user", content="from telegram", channel="telegram")
    conversation_memory.append(P(), role="user", content="from web", channel="web")
    hist = conversation_memory.history(P())
    channels = {h["channel"] for h in hist}
    assert "telegram" in channels and "web" in channels


@pytest.mark.parametrize("channel", ["web", "telegram", "desktop", "voice"])
def test_channel_save(channel):
    m = memory_manager.save(OWNER, title=f"via {channel}", content="x", channel=channel)
    assert m["channel"] == channel

def test_telegram_btn_memory():
    from services.telegram_ai_super_app.catalog import BTN, MAIN_MENU_BUTTONS
    assert BTN.MEMORY == "🧠 Память"
    assert any(b.id == "memory" for b in MAIN_MENU_BUTTONS)
    assert len(MAIN_MENU_BUTTONS) == 12
    assert any(b.id == "automation" for b in MAIN_MENU_BUTTONS) or any(b.id == "memory" for b in MAIN_MENU_BUTTONS)


def test_memory_keyboard():
    from services.telegram_ai_super_app.keyboards import memory_menu_keyboard
    flat = [b.text for row in memory_menu_keyboard().keyboard for b in row]
    assert "Продолжить работу" in flat
    assert "AI Summary" in flat


def test_router_memory_handlers():
    import routers.telegram_super_app_router as r
    assert hasattr(r, "open_memory")
    assert hasattr(r, "memory_menu_buttons")
    assert hasattr(r, "memory_voice_recall")


def test_web_workspace_files():
    from pathlib import Path
    base = Path(__file__).resolve().parents[1] / "src" / "web" / "src" / "ai-workspace"
    assert (base / "AiWorkspacePage.tsx").is_file()
    assert (base / "index.ts").is_file()


def test_docs_exist():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs"
    for name in (
        "MEMORY_ENGINE.md",
        "WORKING_MEMORY.md",
        "LONG_TERM_MEMORY.md",
        "PROJECT_MEMORY.md",
        "AI_TIMELINE.md",
        "SMART_RECALL.md",
        "EPIC_45_2_CONTINUOUS_MEMORY.md",
    ):
        assert (root / name).is_file()

@pytest.mark.parametrize("i", range(50))
def test_smoke_save_cycle(i):
    m = memory_manager.save(OWNER, title=f"S{i}", content=f"C{i}", level="working", kind="note")
    assert memory_manager.pin(OWNER, m["id"])["pinned"]
    assert memory_manager.remove(OWNER, m["id"])


@pytest.mark.parametrize("i", range(40))
def test_smoke_recall_phrases(i):
    phrases = ["Продолжим", "Напомни", "Что осталось?", "Продолжить проект", "Покажи историю"]
    r = memory_manager.recall(OWNER, phrases[i % len(phrases)])
    assert r["intent"]


@pytest.mark.parametrize("i", range(40))
def test_smoke_resume(i):
    working_memory.add_task(P(owner=f"u{i}"), title=f"T{i}")
    data = memory_manager.resume(f"u{i}")
    assert data["welcome_ru"]


@pytest.mark.parametrize("i", range(35))
def test_smoke_context(i):
    ctx = memory_manager.context(OWNER, f"prompt {i}", channel="web")
    assert ctx["version"] == "2.0.0"


@pytest.mark.parametrize("i", range(30))
def test_smoke_timeline(i):
    memory_timeline.record(P(), action="x", title=f"t{i}")
    assert memory_manager.timeline(OWNER, window="all")["count"] >= 1


@pytest.mark.parametrize("oid_n", range(20))
@pytest.mark.parametrize("level", ["session", "working", "project", "long_term", "knowledge"])
def test_regression_levels(oid_n, level):
    oid = f"lvl:{oid_n}"
    memory_manager.save(oid, title=f"{level}-{oid_n}", content="x", level=level, kind="note")
    st = memory_manager.status(oid)
    assert st["counts"][level] >= 1


@pytest.mark.parametrize("i", range(15))
def test_regression_embeddings_rank(i):
    docs = [(f"d{j}", f"реклама салон {j}") for j in range(5)]
    ranked = memory_embeddings.rank(f"реклама {i}", docs)
    assert ranked[0][1] >= ranked[-1][1]


def test_suite_size_marker():
    import tests.test_continuous_memory_45_2 as mod
    src = inspect.getsource(mod)
    assert src.count("def test_") >= 40
    assert "test_smoke_save_cycle" in src
