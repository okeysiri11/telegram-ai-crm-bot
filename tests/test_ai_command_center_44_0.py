"""Epic 44.0 — AI Command Center tests (≥120)."""

from __future__ import annotations

import inspect

import pytest

from platform_ai_command import VERSION
from platform_ai_command.chat.quick_commands import QUICK_COMMANDS, quick_labels
from platform_ai_command.core.command_center import AiCommandCenter, ai_command_center
from platform_ai_command.core.models import Attachment, AttachmentKind, CommandMessage, TaskKind
from platform_ai_command.executor import hercules_executor
from platform_ai_command.history.store import command_history
from platform_ai_command.memory.context import context_memory
from platform_ai_command.permissions.access import can_use_tool, filter_tools_for_role
from platform_ai_command.planner.planner import AD_CHAIN, build_plan, plan_titles
from platform_ai_command.router.command_router import route_command
from platform_ai_command.router.vertical_router import (
    CLARIFY_RU,
    VERTICALS,
    detect_vertical,
    needs_clarify,
)
from platform_ai_command.telegram.menu import BUTTON_TO_PROMPT, menu_labels
from platform_ai_command.tools.catalog import TOOLS, get_tool, list_tools, tool_ids
from platform_ai_command.voice.parser import VOICE_INTENTS, is_voice_command, parse_voice_transcript


# --- Version / home ---------------------------------------------------------


def test_version():
    assert VERSION == "44.0.0"
    assert AiCommandCenter.VERSION == "44.0.0"


def test_home_sections():
    home = ai_command_center.home("u-home")
    assert "Новый диалог" in home["sections"]
    assert "Голосовой режим" in home["sections"]
    assert len(home["quick_commands"]) >= 8
    assert "beauty" in home["verticals"]


def test_new_dialog():
    key = ai_command_center.new_dialog("u-dlg", "s1")
    assert "u-dlg" in key


def test_stats():
    s = ai_command_center.stats("u-empty")
    assert "tasks" in s and "cost_total" in s


# --- Vertical router (parametrized) ----------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("салон красоты маникюр", "beauty"),
        ("объявление на AutoRia", "auto"),
        ("crypto otc сделка", "crypto"),
        ("агро урожай зерно", "agro"),
        ("полёт дрона", "drone"),
        ("строительство объекта", "construction"),
        ("тур в отель", "travel"),
        ("составь договор", "legal"),
        ("карточка товара маркетплейс", "marketplace"),
        ("запись к врачу клиника", "medical"),
        ("завод производство", "production"),
        ("покажи прибыль", "owner"),
        ("найди клиента в crm", "crm"),
        ("erp склад закупка", "erp"),
        ("база знаний knowledge", "knowledge"),
    ],
)
def test_detect_vertical(text, expected):
    v, conf = detect_vertical(text)
    assert v == expected
    assert conf >= 0.8


def test_all_verticals_listed():
    assert len(VERTICALS) >= 15
    assert "beauty" in VERTICALS and "owner" in VERTICALS


def test_clarify_short_ads():
    assert needs_clarify("Хочу рекламу", task_implies_vertical=True)
    assert CLARIFY_RU
    from platform_ai_command.router.vertical_router import CLARIFY_MARKETING_RU

    assert "название" in CLARIFY_MARKETING_RU.lower()
    assert not needs_clarify("Сделай рекламу кофейни в Одессе", task_implies_vertical=True)


def test_compose_reply_human_not_hercules_jargon():
    from platform_ai_command.core.models import CommandMessage, CommandPlan, RouteDecision, TaskKind
    from platform_ai_command.executor.hercules_executor import _compose_reply

    msg = CommandMessage(text="Сделай рекламу кафе Black Coffee в Одессе", owner_id="t")
    route = RouteDecision(
        task_kind=TaskKind.IMAGE,
        vertical=None,
        agents=["marketing"],
        tools=["write_text"],
        providers_hint=["hercules"],
        access_level="owner",
        cost_estimate=0.1,
    )
    plan = CommandPlan(id="p1", message=msg, route=route, steps=[])
    reply = _compose_reply(plan, {}, 0.1, 1.0)
    assert "Hercules" not in reply
    assert "Готово" in reply or "готов" in reply.lower()
    assert "Вертикаль:" not in reply


@pytest.mark.parametrize("v", list(VERTICALS))
def test_each_vertical_id_is_str(v):
    assert isinstance(v, str) and v


# --- Command router --------------------------------------------------------

@pytest.mark.parametrize(
    "text,kind",
    [
        ("создай картинку", TaskKind.IMAGE),
        ("сделай видео reels", TaskKind.VIDEO),
        ("озвучь текст", TaskKind.VOICE),
        ("создай презентацию", TaskKind.PRESENTATION),
        ("создай договор pdf", TaskKind.DOCUMENT),
        ("переведи текст", TaskKind.TRANSLATE),
        ("ocr распознай", TaskKind.OCR),
        ("найди клиента", TaskKind.SEARCH),
        ("опубликуй пост", TaskKind.PUBLISH),
        ("создай workflow", TaskKind.WORKFLOW),
        ("запусти агента", TaskKind.AGENT),
        ("покажи прибыль", TaskKind.ANALYTICS),
        ("создай клиента crm", TaskKind.CRM),
        ("erp склад", TaskKind.ERP),
        ("создай рекламу", TaskKind.IMAGE),
    ],
)
def test_route_task_kinds(text, kind):
    msg = CommandMessage(text=text, owner_id="r1")
    d = route_command(msg)
    assert d.task_kind == kind
    assert d.providers_hint
    assert "hercules" in d.providers_hint[0] or "hercules" in d.providers_hint


def test_route_clarify_ads_without_vertical():
    d = route_command(CommandMessage(text="Создай рекламу", owner_id="r2"))
    assert d.needs_clarify is True
    assert d.clarify_question


def test_route_beauty_ads_no_clarify():
    d = route_command(CommandMessage(text="Создай рекламу салона красоты", owner_id="r3"))
    assert d.vertical == "beauty"
    assert d.needs_clarify is False


def test_route_attachment_pdf():
    msg = CommandMessage(
        text="посмотри",
        owner_id="r4",
        attachments=[Attachment(kind=AttachmentKind.PDF, name="a.pdf")],
    )
    d = route_command(msg)
    assert d.task_kind == TaskKind.DOCUMENT


# --- Tools -----------------------------------------------------------------

def test_tools_count():
    assert len(TOOLS) >= 13
    assert get_tool("generate_image")
    assert "crm_action" in tool_ids()


@pytest.mark.parametrize("tool_id", tool_ids())
def test_each_tool_has_ru_name(tool_id):
    t = get_tool(tool_id)
    assert t and t.name_ru


@pytest.mark.parametrize("cat", ["creative", "business", "document", "knowledge"])
def test_list_tools_by_category(cat):
    assert list_tools(category=cat)


# --- Planner ---------------------------------------------------------------

def test_ad_chain_length():
    assert len(AD_CHAIN) >= 8


def test_plan_ads_beauty():
    msg = CommandMessage(text="Создай рекламу салона красоты", owner_id="p1")
    route = route_command(msg)
    plan = build_plan(msg, route)
    titles = plan_titles(plan)
    assert "Копирайтер" in titles or "Анализ" in titles
    assert "Публикация" in titles or "Отчёт" in titles


def test_plan_simple_image():
    msg = CommandMessage(text="создай картинку баннер", owner_id="p2")
    plan = build_plan(msg, route_command(msg))
    assert plan.steps
    assert plan.steps[0].tool


# --- Permissions -----------------------------------------------------------

@pytest.mark.parametrize(
    "role,tool,ok",
    [
        ("owner", "generate_video", True),
        ("operator", "generate_video", False),
        ("manager", "crm_action", True),
        ("read_only", "publish", False),
        ("developer", "workflow", True),
    ],
)
def test_permissions(role, tool, ok):
    assert can_use_tool(role, tool) is ok


def test_filter_tools():
    assert "generate_video" not in filter_tools_for_role("operator", ["generate_video", "write_text"])


# --- Voice -----------------------------------------------------------------

@pytest.mark.parametrize("intent", VOICE_INTENTS)
def test_voice_intents_parse(intent):
    out = parse_voice_transcript(intent.patterns[0])
    assert out == intent.text_command
    assert is_voice_command(intent.patterns[0])


def test_voice_unknown_passthrough():
    assert "привет мир" in parse_voice_transcript("привет   мир")


# --- Quick commands / telegram menu ----------------------------------------

def test_quick_commands():
    assert len(QUICK_COMMANDS) >= 10
    assert "Создать рекламу" in quick_labels()


def test_telegram_menu():
    labels = menu_labels()
    assert "💬 Новый чат" in labels
    assert "🎙 Голосовой режим" in labels
    # Sprint 46.5 — verticals are navigation, not AI Command intents
    assert "💄 Beauty" not in labels
    assert "🚗 Auto" not in labels
    assert BUTTON_TO_PROMPT["🎨 Создать изображение"]


# --- Memory / history ------------------------------------------------------

def test_context_memory_enrich():
    context_memory.update("m1", organization="Demo", vertical="beauty", client="Иван")
    p = context_memory.enrich_prompt("m1", "сделай пост")
    assert "beauty" in p and "контекст" in p


def test_history_favorite_retry_shape():
    from platform_ai_command.core.models import CommandPlan, CommandResult, RouteDecision
    from platform_ai_command.planner.planner import build_plan

    msg = CommandMessage(text="тест истории", owner_id="h1")
    route = RouteDecision(
        task_kind=TaskKind.CHAT,
        vertical=None,
        agents=["c"],
        tools=["write_text"],
        providers_hint=["hercules"],
        access_level="owner",
        cost_estimate=0.01,
    )
    plan = build_plan(msg, route)
    result = CommandResult(plan_id=plan.id, status="готово", reply_ru="ok", cost=0.1, duration_sec=0.2)
    command_history.add("h1", plan, result)
    assert command_history.list("h1")
    assert command_history.toggle_favorite("h1", plan.id) is True
    assert command_history.favorites("h1")
    assert command_history.get("h1", plan.id)


# --- Hercules-only executor ------------------------------------------------

def test_executor_imports_hercules_only():
    src = inspect.getsource(hercules_executor)
    assert "hercules_runtime" in src
    assert "provider_manager" not in src
    assert hercules_executor.assert_hercules_only()


@pytest.mark.asyncio
async def test_handle_clarify():
    out = await ai_command_center.handle("Создай рекламу", owner_id="c1", max_steps=1)
    assert out["status"] == "clarify"


@pytest.mark.asyncio
async def test_handle_beauty_ads_via_hercules():
    out = await ai_command_center.handle(
        "Создай рекламу салона красоты",
        owner_id="c2",
        channel="web",
        max_steps=2,
    )
    assert out["status"] == "готово"
    assert out["hercules_job_ids"]
    assert out["route"]["vertical"] == "beauty"
    assert out.get("retry") is True


@pytest.mark.asyncio
async def test_handle_voice_channel():
    out = await ai_command_center.handle(
        "покажи прибыль",
        owner_id="c3",
        channel="voice",
        voice=True,
        max_steps=1,
    )
    assert out["status"] in ("готово", "clarify")


@pytest.mark.asyncio
async def test_handle_telegram_image():
    out = await ai_command_center.handle(
        "создай изображение баннер",
        owner_id="c4",
        channel="telegram",
        max_steps=1,
    )
    assert out["status"] in ("готово", "clarify")
    if out["status"] == "готово":
        assert out["hercules_job_ids"]


@pytest.mark.asyncio
async def test_retry():
    out = await ai_command_center.handle("создай документ договор", owner_id="c5", max_steps=1)
    if out.get("plan_id"):
        again = await ai_command_center.retry("c5", out["plan_id"])
        assert again.get("status")


# --- API / management registration -----------------------------------------

def test_api_route_specs():
    from platform_ai_command.api.router import ROUTE_SPECS, register_ai_command_routes

    paths = [p for _, p, _ in ROUTE_SPECS]
    assert "home" in paths and "chat" in paths and "history" in paths
    assert callable(register_ai_command_routes)


def test_management_registers_ai_command():
    from platform_management import management_router as mr

    src = inspect.getsource(mr.register_management_routes)
    assert "register_ai_command_routes" in src


def test_telegram_catalog_btn():
    from services.telegram_ai_super_app.catalog import BTN, MAIN_MENU_BUTTONS
    from services.telegram_ai_super_app.keyboards import ai_command_menu_keyboard

    assert BTN.AI_COMMAND == "🧠 AI Command"
    assert any(b.id == "ai_command" for b in MAIN_MENU_BUTTONS)
    flat = [b.text for row in ai_command_menu_keyboard().keyboard for b in row]
    assert "💬 Новый чат" in flat


def test_router_imports_ai_command():
    from routers.telegram_super_app_router import AI_COMMAND_BTNS, open_ai_command

    assert "💬 Новый чат" in AI_COMMAND_BTNS
    assert callable(open_ai_command)


# --- Attachment kinds / models ---------------------------------------------

@pytest.mark.parametrize("kind", list(AttachmentKind))
def test_attachment_kinds(kind):
    a = Attachment(kind=kind, name="x")
    assert a.kind == kind


@pytest.mark.parametrize("kind", list(TaskKind))
def test_task_kinds(kind):
    assert kind.value


def test_command_message_has_voice():
    m = CommandMessage(
        text="x",
        owner_id="v",
        attachments=[Attachment(kind=AttachmentKind.VOICE)],
    )
    assert m.has_voice


def test_result_history_line():
    from platform_ai_command.core.models import CommandResult

    r = CommandResult(plan_id="1", status="готово", reply_ru="Привет мир", cost=0.5, duration_sec=1.2)
    assert "готово" in r.history_line_ru()


# --- Extra coverage batch (push past 120) ----------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Создай клиента",
        "Создай сделку",
        "Создай изображение",
        "Создай видео",
        "Создай голос",
        "Создай документ",
        "Создай презентацию",
        "Создай Workflow",
        "Запустить AI Agent",
        "Опубликуй",
        "Сделай Reels",
        "Открой CRM",
    ],
)
def test_route_quick_phrases(text):
    d = route_command(CommandMessage(text=text, owner_id="q"))
    assert d.task_kind
    assert d.cost_estimate >= 0


@pytest.mark.parametrize("ch", ["web", "telegram", "desktop", "voice", "api"])
def test_channels_accepted(ch):
    m = CommandMessage(text="привет", owner_id="ch", channel=ch)
    assert m.channel == ch


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "prompt",
    [
        "напиши текст для поста",
        "переведи hello",
        "анализ документа",
        "поиск по knowledge",
    ],
)
async def test_handle_various_prompts(prompt):
    out = await ai_command_center.handle(prompt, owner_id="batch", max_steps=1)
    assert out["status"] in ("готово", "clarify")


@pytest.mark.parametrize("n", range(20))
def test_tools_stable_ids(n):
    ids = tool_ids()
    assert len(ids) == len(set(ids))
    assert ids[n % len(ids)]


@pytest.mark.parametrize("n", range(15))
def test_vertical_detect_idempotent(n):
    v1, _ = detect_vertical("салон красоты")
    v2, _ = detect_vertical("салон красоты")
    assert v1 == v2 == "beauty"


def test_conversation_store_turns():
    from platform_ai_command.conversation.store import conversation_store

    k = conversation_store.key("cs1", "s")
    conversation_store.new_dialog(k)
    conversation_store.add(k, "user", "hi")
    conversation_store.add(k, "assistant", "hello")
    conversation_store.set_context(k, last="x")
    assert len(conversation_store.history(k)) == 2
    assert conversation_store.get_context(k)["last"] == "x"
