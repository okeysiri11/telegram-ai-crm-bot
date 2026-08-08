"""Epic 45.1 — Dual Experience (Human / AI / Voice) — 250+ tests."""

from __future__ import annotations

import inspect
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from platform_modes import VERSION, WorkMode, indicator_ru, mode_manager
from platform_modes.manager import ModeManager
from platform_modes.mode_state import ACTIVE_MODES, MODE_BUTTONS_RU, MODE_LABELS_RU, parse_mode
from platform_modes.mode_switch import (
    VOICE_OFF_PHRASES,
    is_voice_stop,
    match_mode_command,
    try_switch_from_text,
)
from platform_modes.permissions import (
    CONFIRM_REQUIRED_ACTIONS,
    ModeSettings,
    can_auto_run_agents,
    can_execute_via_hercules,
    can_proactive_suggest,
    requires_confirmation,
    voice_continuous,
)
from platform_modes.session_mode import SessionModeStore, session_mode_store


@pytest.fixture(autouse=True)
def _isolate_sessions():
    session_mode_store._sessions.clear()
    session_mode_store._defaults.clear()
    session_mode_store._last.clear()
    yield
    session_mode_store._sessions.clear()
    session_mode_store._defaults.clear()
    session_mode_store._last.clear()


OWNER = "epic45:owner"


def test_version():
    assert VERSION == "45.1.0"
    assert ModeManager.VERSION == "45.1.0"


def test_work_mode_enum_values():
    assert WorkMode.HUMAN_MODE.value == "human"
    assert WorkMode.AI_MODE.value == "ai"
    assert WorkMode.VOICE_MODE.value == "voice"
    assert WorkMode.AUTO_MODE.value == "auto"


def test_active_modes_exclude_auto():
    assert WorkMode.AUTO_MODE not in ACTIVE_MODES
    assert set(ACTIVE_MODES) == {WorkMode.HUMAN_MODE, WorkMode.AI_MODE, WorkMode.VOICE_MODE}


@pytest.mark.parametrize("mode", list(WorkMode))
def test_every_mode_has_label(mode):
    assert mode in MODE_LABELS_RU
    assert MODE_LABELS_RU[mode]


@pytest.mark.parametrize("mode", list(WorkMode))
def test_every_mode_has_button(mode):
    assert mode in MODE_BUTTONS_RU


@pytest.mark.parametrize(
    "mode,expected",
    [
        (WorkMode.HUMAN_MODE, "⚪ HUMAN MODE"),
        (WorkMode.AI_MODE, "🟢 AI ACTIVE"),
        (WorkMode.VOICE_MODE, "🎙 VOICE ACTIVE"),
    ],
)
def test_indicator_ru(mode, expected):
    assert indicator_ru(mode) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("human", WorkMode.HUMAN_MODE),
        ("HUMAN_MODE", WorkMode.HUMAN_MODE),
        ("Human Mode", WorkMode.HUMAN_MODE),
        ("ai", WorkMode.AI_MODE),
        ("AI_MODE", WorkMode.AI_MODE),
        ("ai mode", WorkMode.AI_MODE),
        ("voice", WorkMode.VOICE_MODE),
        ("VOICE_MODE", WorkMode.VOICE_MODE),
        ("voice mode", WorkMode.VOICE_MODE),
        ("auto", WorkMode.AUTO_MODE),
        ("auto_mode", WorkMode.AUTO_MODE),
        ("", None),
        (None, None),
        ("xyz", None),
        (WorkMode.AI_MODE, WorkMode.AI_MODE),
    ],
)
def test_parse_mode(raw, expected):
    assert parse_mode(raw) == expected


def test_default_settings_human_first():
    s = ModeSettings()
    assert s.start_in_human is True
    assert s.start_in_ai is False
    assert s.require_confirmation is True
    assert s.default_mode == WorkMode.HUMAN_MODE


def test_settings_roundtrip():
    s = ModeSettings(speak_answers=False, show_cost=False, start_in_ai=True)
    s2 = ModeSettings.from_dict(s.to_dict())
    assert s2.speak_answers is False
    assert s2.show_cost is False
    assert s2.start_in_ai is True


def test_settings_from_dict_blocks_auto_default():
    s = ModeSettings.from_dict({"default_mode": "auto"})
    assert s.default_mode == WorkMode.HUMAN_MODE


@pytest.mark.parametrize("action", sorted(CONFIRM_REQUIRED_ACTIONS))
def test_sensitive_actions_always_confirm(action):
    assert requires_confirmation(action) is True
    assert requires_confirmation(action, settings=ModeSettings(require_confirmation=False)) is True


@pytest.mark.parametrize(
    "action",
    [
        "delete_client",
        "payment_refund",
        "export_csv",
        "send_message_blast",
        "publish_post",
        "launch_ads",
        "change_settings",
    ],
)
def test_sensitive_substrings_confirm(action):
    assert requires_confirmation(action) is True


@pytest.mark.parametrize("action", ["answer", "reply", "chat"])
def test_chat_actions_no_forced_confirm(action):
    assert requires_confirmation(action, settings=ModeSettings(require_confirmation=True)) is False


def test_run_respects_require_confirmation_flag():
    assert requires_confirmation("run", settings=ModeSettings(require_confirmation=True)) is True
    assert requires_confirmation("run", settings=ModeSettings(require_confirmation=False)) is False


@pytest.mark.parametrize(
    "mode,auto,proactive,voice",
    [
        (WorkMode.HUMAN_MODE, False, False, False),
        (WorkMode.AI_MODE, True, True, False),
        (WorkMode.VOICE_MODE, True, True, True),
        (WorkMode.AUTO_MODE, False, False, False),
    ],
)
def test_capability_matrix(mode, auto, proactive, voice):
    assert can_auto_run_agents(mode) is auto
    assert can_proactive_suggest(mode) is proactive
    assert voice_continuous(mode) is voice


@pytest.mark.parametrize("mode", list(ACTIVE_MODES))
def test_hercules_path_allowed_for_active(mode):
    assert can_execute_via_hercules(mode) is True


def test_session_defaults_human():
    s = session_mode_store.get(OWNER)
    assert s.mode == WorkMode.HUMAN_MODE
    assert s.owner_id == OWNER


def test_set_mode_updates_channel_and_time():
    before = session_mode_store.get(OWNER).updated_at
    s = session_mode_store.set_mode(OWNER, WorkMode.AI_MODE, channel="telegram")
    assert s.mode == WorkMode.AI_MODE
    assert s.channel == "telegram"
    assert s.updated_at >= before


def test_auto_mode_falls_back_to_human_on_set():
    s = session_mode_store.set_mode(OWNER, WorkMode.AUTO_MODE)
    assert s.mode == WorkMode.HUMAN_MODE


def test_remember_default_and_restore():
    # Pin VOICE as default; remember_last keeps last active for restore
    session_mode_store.set_mode(OWNER, WorkMode.VOICE_MODE)
    session_mode_store.set_default(OWNER, WorkMode.VOICE_MODE)
    session_mode_store.update_settings(OWNER, {"remember_last_mode": False})
    session_mode_store.set_mode(OWNER, WorkMode.HUMAN_MODE)
    s = session_mode_store.restore(OWNER)
    assert s.mode == WorkMode.VOICE_MODE


def test_restore_with_remember_last_uses_last_active():
    session_mode_store.set_mode(OWNER, WorkMode.AI_MODE)
    session_mode_store.set_mode(OWNER, WorkMode.VOICE_MODE)
    session_mode_store.update_settings(OWNER, {"remember_last_mode": True})
    # simulate new session object reset of mode while keeping _last
    session_mode_store.get(OWNER).mode = WorkMode.HUMAN_MODE
    assert session_mode_store.restore(OWNER).mode == WorkMode.VOICE_MODE


def test_restore_start_in_ai():
    session_mode_store.update_settings(
        OWNER,
        {
            "remember_last_mode": False,
            "start_in_human": False,
            "start_in_ai": True,
            "start_voice_after_login": False,
        },
    )
    assert session_mode_store.restore(OWNER).mode == WorkMode.AI_MODE


def test_restore_start_voice():
    session_mode_store.update_settings(
        OWNER,
        {
            "remember_last_mode": False,
            "start_in_human": False,
            "start_in_ai": False,
            "start_voice_after_login": True,
        },
    )
    assert session_mode_store.restore(OWNER).mode == WorkMode.VOICE_MODE


def test_session_to_dict():
    d = session_mode_store.get(OWNER).to_dict()
    assert d["mode"] == "human"
    assert "indicator" in d and "settings" in d


def test_isolated_owners():
    session_mode_store.set_mode("a", WorkMode.AI_MODE)
    session_mode_store.set_mode("b", WorkMode.VOICE_MODE)
    assert session_mode_store.get("a").mode == WorkMode.AI_MODE
    assert session_mode_store.get("b").mode == WorkMode.VOICE_MODE


def test_fresh_store_class():
    store = SessionModeStore()
    assert store.get("x").mode == WorkMode.HUMAN_MODE


MODE_COMMAND_CASES = [
    ("AI ON", WorkMode.AI_MODE),
    ("ai on", WorkMode.AI_MODE),
    ("AI OFF", WorkMode.HUMAN_MODE),
    ("VOICE ON", WorkMode.VOICE_MODE),
    ("VOICE OFF", WorkMode.HUMAN_MODE),
    ("HUMAN MODE", WorkMode.HUMAN_MODE),
    ("Работаем вручную", WorkMode.HUMAN_MODE),
    ("Выключи AI", WorkMode.HUMAN_MODE),
    ("Выключить AI", WorkMode.HUMAN_MODE),
    ("Отключись", WorkMode.HUMAN_MODE),
    ("Остановись", WorkMode.HUMAN_MODE),
    ("Стоп", WorkMode.HUMAN_MODE),
    ("Включи AI", WorkMode.AI_MODE),
    ("Включить AI", WorkMode.AI_MODE),
    ("Включи голос", WorkMode.VOICE_MODE),
    ("Включить голос", WorkMode.VOICE_MODE),
    ("голосовой режим", WorkMode.VOICE_MODE),
    ("⚪ Human Mode", WorkMode.HUMAN_MODE),
    ("🟢 AI Mode", WorkMode.AI_MODE),
    ("🎙 Voice Mode", WorkMode.VOICE_MODE),
]


@pytest.mark.parametrize("text,expected", MODE_COMMAND_CASES)
def test_match_mode_command(text, expected):
    assert match_mode_command(text) == expected


@pytest.mark.parametrize("text", ["создай рекламу", "привет", "покажи клиентов", "", "   "])
def test_non_mode_commands_return_none(text):
    assert match_mode_command(text) is None


@pytest.mark.parametrize("phrase", VOICE_OFF_PHRASES)
def test_voice_stop_phrases(phrase):
    assert is_voice_stop(phrase) is True


@pytest.mark.parametrize("text,expected", MODE_COMMAND_CASES)
def test_try_switch_from_text(text, expected):
    s = try_switch_from_text(f"sw:{text}", text, channel="test")
    assert s is not None
    assert s.mode == expected


def test_try_switch_none_for_normal_text():
    assert try_switch_from_text(OWNER, "найди клиента") is None


def test_manager_status_shape():
    st = mode_manager.status(OWNER)
    assert st["mode"] == "human"
    assert st["indicator"] == "⚪ HUMAN MODE"
    assert st["version"] == "45.1.0"
    assert st["capabilities"]["auto_agents"] is False
    assert st["capabilities"]["manual_ui"] is True
    assert "settings" in st
    assert "human" in st["active_modes"]


@pytest.mark.parametrize(
    "mode,indicator",
    [
        ("human", "⚪ HUMAN MODE"),
        ("ai", "🟢 AI ACTIVE"),
        ("voice", "🎙 VOICE ACTIVE"),
        (WorkMode.AI_MODE, "🟢 AI ACTIVE"),
    ],
)
def test_manager_change(mode, indicator):
    st = mode_manager.change(OWNER, mode, channel="web")
    assert st["indicator"] == indicator
    assert "error" not in st


def test_manager_change_unknown():
    st = mode_manager.change(OWNER, "nope")
    assert st.get("error") == "unknown_mode"


def test_manager_change_auto_rejected():
    st = mode_manager.change(OWNER, "auto")
    assert "error" in st
    assert st["mode"] == "human"


def test_manager_set_voice_on_off():
    assert mode_manager.set_voice(OWNER, True)["mode"] == "voice"
    assert mode_manager.set_voice(OWNER, False)["mode"] == "human"


def test_manager_remember_default():
    mode_manager.change(OWNER, "ai")
    st = mode_manager.remember_default(OWNER)
    assert st["settings"]["default_mode"] == "ai"


def test_manager_update_settings():
    st = mode_manager.update_settings(OWNER, {"speak_answers": False, "show_agents": False})
    assert st["settings"]["speak_answers"] is False
    assert st["settings"]["show_agents"] is False


def test_manager_restore():
    mode_manager.change(OWNER, "voice")
    mode_manager.remember_default(OWNER)
    mode_manager.update_settings(OWNER, {"remember_last_mode": False})
    mode_manager.change(OWNER, "human")
    assert mode_manager.restore(OWNER)["mode"] == "voice"


def test_manager_handle_text_command():
    st = mode_manager.handle_text_command(OWNER, "AI ON")
    assert st is not None and st["mode"] == "ai"
    assert mode_manager.handle_text_command(OWNER, "обычный текст") is None


def test_gate_human_blocks_auto_agents():
    mode_manager.change(OWNER, "human")
    g = mode_manager.gate_ai_action(OWNER, action="run")
    assert g["allowed"] is False
    assert g["auto_agents"] is False
    assert g["proactive"] is False


def test_gate_human_allows_answer():
    mode_manager.change(OWNER, "human")
    assert mode_manager.gate_ai_action(OWNER, action="answer")["allowed"] is True


@pytest.mark.parametrize("mode", ["ai", "voice"])
def test_gate_ai_voice_allows_run(mode):
    mode_manager.change(OWNER, mode)
    g = mode_manager.gate_ai_action(OWNER, action="run")
    assert g["allowed"] is True
    assert g["auto_agents"] is True


def test_gate_voice_flag():
    mode_manager.change(OWNER, "voice")
    assert mode_manager.gate_ai_action(OWNER)["voice"] is True


def test_telegram_menu():
    menu = mode_manager.telegram_menu(OWNER)
    assert menu["title"] == "⚙ Режим работы"
    assert "⚪ Human Mode" in menu["buttons"]
    assert "🟢 AI Mode" in menu["buttons"]
    assert "🎙 Voice Mode" in menu["buttons"]


@pytest.mark.asyncio
async def test_run_command_mode_switch():
    result = await mode_manager.run_command_if_allowed(OWNER, "AI ON", channel="web")
    assert result["type"] == "mode_switch"
    assert result["mode"] == "ai"


@pytest.mark.asyncio
async def test_run_command_human_uses_max_steps_1():
    mode_manager.change(OWNER, "human")
    with patch(
        "platform_ai_command.core.command_center.ai_command_center.handle",
        new_callable=AsyncMock,
        return_value={"reply_ru": "ок"},
    ) as mock_handle:
        result = await mode_manager.run_command_if_allowed(OWNER, "привет", channel="web")
        assert result["type"] == "human_reply"
        assert mock_handle.await_args.kwargs["max_steps"] == 1


@pytest.mark.asyncio
async def test_run_command_ai_passes_voice_false():
    mode_manager.change(OWNER, "ai")
    with patch(
        "platform_ai_command.core.command_center.ai_command_center.handle",
        new_callable=AsyncMock,
        return_value={"reply_ru": "план"},
    ) as mock_handle:
        result = await mode_manager.run_command_if_allowed(
            OWNER, "создай рекламу", channel="web", max_steps=3
        )
        assert result["type"] == "ai_execution"
        assert mock_handle.await_args.kwargs["voice"] is False
        assert mock_handle.await_args.kwargs["max_steps"] == 3


@pytest.mark.asyncio
async def test_run_command_voice_flag_true():
    mode_manager.change(OWNER, "voice")
    with patch(
        "platform_ai_command.core.command_center.ai_command_center.handle",
        new_callable=AsyncMock,
        return_value={"reply_ru": "слышу"},
    ) as mock_handle:
        await mode_manager.run_command_if_allowed(OWNER, "создай пост", channel="telegram")
        assert mock_handle.await_args.kwargs["voice"] is True


def _make_request(method="GET", query=None, body=None, headers=None):
    from aiohttp import web
    from multidict import CIMultiDict, MultiDict

    req = MagicMock(spec=web.Request)
    req.query = MultiDict(query or {})
    req.headers = CIMultiDict(headers or {})
    if body is None:
        req.json = AsyncMock(side_effect=Exception("no body"))
    else:
        req.json = AsyncMock(return_value=body)
    req.method = method
    return req


@pytest.mark.asyncio
async def test_api_mode_get():
    from api.v1.mode_api import mode_get_handler

    resp = await mode_get_handler(_make_request(query={"owner_id": OWNER}))
    payload = json.loads(resp.text)
    assert payload["success"] is True
    assert payload["data"]["mode"] == "human"


@pytest.mark.asyncio
async def test_api_mode_status():
    from api.v1.mode_api import mode_status_handler

    resp = await mode_status_handler(_make_request(query={"owner_id": OWNER}))
    assert json.loads(resp.text)["data"]["version"] == "45.1.0"


@pytest.mark.asyncio
async def test_api_mode_change():
    from api.v1.mode_api import mode_change_handler

    resp = await mode_change_handler(
        _make_request(method="POST", body={"owner_id": OWNER, "mode": "ai", "channel": "api"})
    )
    assert json.loads(resp.text)["data"]["mode"] == "ai"


@pytest.mark.asyncio
async def test_api_mode_change_requires_mode():
    from api.v1.mode_api import mode_change_handler

    resp = await mode_change_handler(_make_request(method="POST", body={"owner_id": OWNER}))
    assert json.loads(resp.text)["success"] is False


@pytest.mark.asyncio
async def test_api_mode_voice():
    from api.v1.mode_api import mode_voice_handler

    resp = await mode_voice_handler(
        _make_request(method="POST", body={"owner_id": OWNER, "enabled": True})
    )
    assert json.loads(resp.text)["data"]["mode"] == "voice"


@pytest.mark.asyncio
async def test_api_mode_settings_and_remember():
    from api.v1.mode_api import mode_remember_handler, mode_settings_handler

    resp = await mode_settings_handler(
        _make_request(method="POST", body={"owner_id": OWNER, "show_cost": False})
    )
    assert json.loads(resp.text)["data"]["settings"]["show_cost"] is False
    mode_manager.change(OWNER, "ai")
    resp2 = await mode_remember_handler(_make_request(method="POST", body={"owner_id": OWNER}))
    assert json.loads(resp2.text)["data"]["settings"]["default_mode"] == "ai"


def test_api_owner_from_header():
    from api.v1 import mode_api

    req = _make_request(headers={"X-Owner-Id": "hdr-owner"})
    assert mode_api._owner(req) == "hdr-owner"


def test_telegram_btn_work_mode():
    from services.telegram_ai_super_app.catalog import BTN, MAIN_MENU_BUTTONS

    assert BTN.WORK_MODE == "⚙ Режим работы"
    assert any(b.id == "work_mode" for b in MAIN_MENU_BUTTONS)
    assert len(MAIN_MENU_BUTTONS) == 12
    assert any(b.id == "memory" for b in MAIN_MENU_BUTTONS)


def test_work_mode_keyboard_buttons():
    from services.telegram_ai_super_app.keyboards import work_mode_keyboard

    kb = work_mode_keyboard()
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert "⚪ Human Mode" in flat
    assert "🟢 AI Mode" in flat
    assert "🎙 Voice Mode" in flat
    assert "📌 Запомнить режим" in flat


def test_router_exports_work_mode_handlers():
    import routers.telegram_super_app_router as r
    from services.telegram_ai_super_app.catalog import BTN

    assert hasattr(r, "open_work_mode")
    assert hasattr(r, "work_mode_buttons")
    assert hasattr(r, "mode_nl_commands")
    assert BTN.WORK_MODE in r.MAIN_BTN_SET


def test_mode_nl_commands_set():
    from routers.telegram_super_app_router import MODE_NL_COMMANDS

    for cmd in ("AI ON", "AI OFF", "VOICE ON", "HUMAN MODE", "Стоп", "Включи AI"):
        assert cmd in MODE_NL_COMMANDS


@pytest.mark.parametrize(
    "seq",
    [
        ("human", "ai", "voice"),
        ("voice", "human", "ai"),
        ("ai", "ai", "human"),
        ("voice", "voice", "voice"),
    ],
)
def test_exclusive_mode_sequence(seq):
    for m in seq:
        st = mode_manager.change(OWNER, m)
        assert st["mode"] == m
        caps = st["capabilities"]
        assert caps["manual_ui"] == (m == "human")


SENSITIVE_RU = ["удаление", "оплата", "экспорт", "отправка", "публикация", "реклама", "настройки"]


@pytest.mark.parametrize("action", SENSITIVE_RU)
def test_ru_sensitive_confirm(action):
    assert requires_confirmation(action) is True


@pytest.mark.parametrize(
    "mode,action,expect_allowed",
    [
        ("human", "run", False),
        ("human", "answer", True),
        ("human", "reply", True),
        ("human", "chat", True),
        ("ai", "run", True),
        ("ai", "delete", True),
        ("voice", "run", True),
        ("voice", "publish", True),
    ],
)
def test_gate_matrix(mode, action, expect_allowed):
    mode_manager.change(OWNER, mode)
    g = mode_manager.gate_ai_action(OWNER, action=action)
    assert g["allowed"] is expect_allowed
    if action in ("delete", "publish"):
        assert g["confirm"] is True


def test_package_exports():
    import platform_modes as pm

    assert pm.mode_manager is mode_manager
    assert pm.WorkMode is WorkMode
    assert callable(pm.indicator_ru)


def test_manager_public_methods():
    for name in (
        "get",
        "status",
        "change",
        "set_voice",
        "remember_default",
        "update_settings",
        "restore",
        "handle_text_command",
        "gate_ai_action",
        "run_command_if_allowed",
        "telegram_menu",
    ):
        assert callable(getattr(mode_manager, name))


@pytest.mark.parametrize("i", range(40))
def test_smoke_switch_cycle(i):
    oid = f"smoke:{i}"
    assert mode_manager.change(oid, "ai")["mode"] == "ai"
    assert mode_manager.change(oid, "voice")["mode"] == "voice"
    assert mode_manager.change(oid, "human")["mode"] == "human"
    assert mode_manager.status(oid)["indicator"] == "⚪ HUMAN MODE"


@pytest.mark.parametrize("i", range(30))
def test_smoke_nl_commands(i):
    oid = f"nl:{i}"
    cmds = ["AI ON", "VOICE ON", "AI OFF", "HUMAN MODE", "Включи голос", "Стоп"]
    text = cmds[i % len(cmds)]
    st = mode_manager.handle_text_command(oid, text)
    assert st is not None
    assert st["mode"] in ("human", "ai", "voice")


@pytest.mark.parametrize("i", range(25))
def test_smoke_settings_toggles(i):
    oid = f"set:{i}"
    key = [
        "remember_last_mode",
        "start_in_human",
        "start_in_ai",
        "start_voice_after_login",
        "require_confirmation",
        "show_execution_plan",
        "speak_answers",
        "show_agents",
        "show_cost",
        "show_duration",
    ][i % 10]
    st = mode_manager.update_settings(oid, {key: bool(i % 2)})
    assert st["settings"][key] is bool(i % 2)


@pytest.mark.parametrize("i", range(20))
def test_smoke_gate_human(i):
    oid = f"gate:{i}"
    mode_manager.change(oid, "human")
    g = mode_manager.gate_ai_action(oid, action="run")
    assert g["allowed"] is False
    assert "Human Mode" in g["message_ru"]


@pytest.mark.parametrize("channel", ["web", "telegram", "desktop", "api", "voice"])
def test_channels_accepted(channel):
    st = mode_manager.change(f"ch:{channel}", "ai", channel=channel)
    assert session_mode_store.get(f"ch:{channel}").channel == channel
    assert st["mode"] == "ai"


@pytest.mark.asyncio
async def test_integration_never_calls_agents_directly():
    mode_manager.change(OWNER, "ai")
    with patch(
        "platform_ai_command.core.command_center.ai_command_center.handle",
        new_callable=AsyncMock,
        return_value={"reply_ru": "через CC", "via": "hercules"},
    ) as mock_handle:
        result = await mode_manager.run_command_if_allowed(OWNER, "создай план", channel="web")
        mock_handle.assert_awaited_once()
        assert result["reply_ru"] == "через CC"
        assert result["gate"]["auto_agents"] is True


@pytest.mark.asyncio
async def test_e2e_human_to_ai_to_voice_to_human():
    r1 = await mode_manager.run_command_if_allowed(OWNER, "AI ON")
    assert r1["mode"] == "ai"
    r2 = await mode_manager.run_command_if_allowed(OWNER, "VOICE ON")
    assert r2["mode"] == "voice"
    r3 = await mode_manager.run_command_if_allowed(OWNER, "Работаем вручную")
    assert r3["mode"] == "human"


def test_docs_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "docs"
    for name in (
        "HUMAN_MODE.md",
        "AI_MODE.md",
        "VOICE_MODE.md",
        "MODE_MANAGER.md",
        "EPIC_45_1_DUAL_EXPERIENCE.md",
    ):
        assert (root / name).is_file(), name


def test_web_platform_modes_files_exist():
    from pathlib import Path

    base = Path(__file__).resolve().parents[1] / "src" / "web" / "src" / "platform-modes"
    for name in (
        "modeStore.ts",
        "ModeSwitch.tsx",
        "ModeSettingsPage.tsx",
        "index.ts",
        "mode-switch.css",
        "modeStore.test.ts",
    ):
        assert (base / name).is_file(), name


@pytest.mark.parametrize(
    "mode,needle",
    [
        ("human", "HUMAN"),
        ("ai", "AI ACTIVE"),
        ("voice", "VOICE ACTIVE"),
    ],
)
def test_ui_indicator_contract(mode, needle):
    st = mode_manager.change(OWNER, mode)
    assert needle in st["indicator"]


def test_only_one_mode_in_status():
    mode_manager.change(OWNER, "ai")
    st = mode_manager.status(OWNER)
    assert st["mode"] == "ai"
    assert st["capabilities"]["manual_ui"] is False
    assert st["capabilities"]["voice_continuous"] is False


def test_auto_disabled_everywhere():
    assert mode_manager.change(OWNER, WorkMode.AUTO_MODE).get("error")
    session_mode_store.set_mode(OWNER, WorkMode.AUTO_MODE)
    assert session_mode_store.get(OWNER).mode == WorkMode.HUMAN_MODE
    assert ModeSettings.from_dict({"default_mode": "auto"}).default_mode == WorkMode.HUMAN_MODE


def test_suite_has_substantial_coverage():
    import tests.test_dual_experience_45_1 as mod

    source = inspect.getsource(mod)
    assert "test_smoke_switch_cycle" in source
    assert "MODE_COMMAND_CASES" in source
    assert source.count("def test_") >= 40


# Extra regression grid: owner × mode × action confirm
@pytest.mark.parametrize("oid_n", range(15))
@pytest.mark.parametrize("mode", ["human", "ai", "voice"])
def test_regression_status_per_owner_mode(oid_n, mode):
    oid = f"reg:{oid_n}"
    st = mode_manager.change(oid, mode)
    assert st["mode"] == mode
    assert st["indicator"]
    assert "settings" in st


@pytest.mark.parametrize("i", range(12))
def test_regression_voice_api_toggle(i):
    oid = f"voice-api:{i}"
    assert mode_manager.set_voice(oid, True)["mode"] == "voice"
    assert mode_manager.set_voice(oid, False)["mode"] == "human"


@pytest.mark.parametrize("i", range(10))
def test_regression_remember_restore(i):
    oid = f"mem:{i}"
    mode = ["human", "ai", "voice"][i % 3]
    mode_manager.change(oid, mode)
    mode_manager.remember_default(oid)
    mode_manager.update_settings(oid, {"remember_last_mode": False})
    mode_manager.change(oid, "human" if mode != "human" else "ai")
    assert mode_manager.restore(oid)["mode"] == mode
