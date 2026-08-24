"""
Sprint 46.5 — vertical navigation bypasses Hercules; role view-as; context isolation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from platform_ai_command.core.models import CommandMessage
from platform_ai_command.memory.context import context_memory
from platform_ai_command.router.command_router import route_command
from platform_ai_command.router.vertical_router import detect_vertical
from platform_ai_command.telegram.menu import BUTTON_TO_PROMPT, menu_labels
from services.vertical_role_registry import (
    PERSONA_LABEL_RU,
    VERTICAL_ENTRY_LABELS,
    vertical_role_registry,
)
from services.vertical_nav_service import (
    clear_stale_vertical_context,
    open_vertical_entry,
    enter_persona_home,
)
from startup import BOT_ROUTER_PATHS


def test_deterministic_actions_before_ai():
    paths = list(BOT_ROUTER_PATHS)
    assert paths.index("routers.vertical_nav_router") < paths.index(
        "routers.telegram_super_app_router"
    )
    assert paths.index("routers.auto_add_vehicle_router") < paths.index(
        "routers.vertical_nav_router"
    )


def test_vertical_buttons_bypass_hercules():
    """Entry labels must not map to BUTTON_TO_PROMPT (Hercules)."""
    for label in ("🚗 Auto", "🌾 Agro", "💄 Beauty", "💰 Crypto"):
        assert label in VERTICAL_ENTRY_LABELS
        assert label not in BUTTON_TO_PROMPT
    labels = menu_labels()
    assert "🚗 Auto" not in labels
    assert "💄 Beauty" not in labels
    assert "🎨 Создать изображение" in labels


def test_vertical_context_switch():
    uid = 4605001
    vertical_role_registry.clear_vertical(uid)
    context_memory.update(str(uid), vertical="beauty")
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    clear_stale_vertical_context(uid, new_vertical="auto")
    sess = vertical_role_registry.get(uid)
    assert sess.active_vertical == "auto"
    assert sess.active_persona is None
    assert context_memory.get(str(uid)).get("vertical") == "auto"


def test_previous_vertical_context_cleared():
    uid = 4605002
    vertical_role_registry.begin_vertical(uid, "beauty")
    vertical_role_registry.set_persona(uid, "owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    clear_stale_vertical_context(uid, new_vertical="auto")
    sess = vertical_role_registry.get(uid)
    assert sess.active_vertical == "auto"
    assert sess.active_persona is None
    assert sess.fsm_state == "vertical_entry"


def test_owner_authorization_preserved():
    uid = 4605003
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    vertical_role_registry.set_persona(uid, "dealer")
    sess = vertical_role_registry.get(uid)
    assert sess.authenticated_role == "platform_owner"
    assert sess.active_persona == "dealer"
    # must not downgrade
    vertical_role_registry.ensure_authenticated_role(uid, "dealer")
    assert vertical_role_registry.get(uid).authenticated_role == "platform_owner"


def test_owner_view_as_role():
    uid = 4605004
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    for persona in ("owner", "dealer", "client"):
        vertical_role_registry.set_persona(uid, persona)
        s = vertical_role_registry.get(uid)
        assert s.active_persona == persona
        assert s.authenticated_role == "platform_owner"
        assert "authenticated_role" in s.ai_context()


def test_auto_role_selector():
    assert vertical_role_registry.personas_for("auto") == ("owner", "dealer", "client")
    assert PERSONA_LABEL_RU["dealer"] == "🚘 Dealer"
    assert VERTICAL_ENTRY_LABELS["🚗 Auto"] == "auto"
    assert VERTICAL_ENTRY_LABELS["🚗 Авто"] == "auto"


def test_agro_role_selector():
    assert vertical_role_registry.personas_for("agro") == ("owner", "trader", "client")
    assert VERTICAL_ENTRY_LABELS["🌾 Agro"] == "agro"
    assert VERTICAL_ENTRY_LABELS["🌾 Agro Trading"] == "agro"


def test_beauty_role_selector():
    assert vertical_role_registry.personas_for("beauty") == (
        "owner",
        "manager",
        "specialist",
        "client",
    )
    assert VERTICAL_ENTRY_LABELS["💄 Beauty"] == "beauty"


def test_navigation_back_stack():
    uid = 4605005
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "agro")
    assert vertical_role_registry.get(uid).fsm_state == "vertical_entry"
    vertical_role_registry.set_persona(uid, "trader")
    assert vertical_role_registry.get(uid).fsm_state == "vertical_home"
    # re-enter selector (simulate back from home)
    vertical_role_registry.begin_vertical(uid, "agro")
    assert vertical_role_registry.get(uid).fsm_state == "vertical_entry"
    vertical_role_registry.clear_vertical(uid)
    assert vertical_role_registry.get(uid).fsm_state == "platform_home"


def test_ai_receives_active_vertical():
    context_memory.update("u-ai", vertical="beauty")
    msg = CommandMessage(
        text="Найди BMW X5 до 15000\n\n[контекст: vertical=beauty]",
        owner_id="u-ai",
        meta={"active_vertical": "auto", "preferred_vertical": "auto"},
    )
    route = route_command(msg)
    assert route.vertical == "auto"


def test_detect_vertical_ignores_context_tag():
    v, _ = detect_vertical("Открой Auto AI\n\n[контекст: vertical=beauty]")
    assert v == "auto"
    v2, _ = detect_vertical("сделай пост", preferred="auto")
    assert v2 == "auto"


@pytest.mark.asyncio
async def test_open_vertical_entry_no_hercules(monkeypatch):
    uid = 4605099
    vertical_role_registry.clear_vertical(uid)
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    monkeypatch.setattr(
        "services.vertical_nav_service._resolve_auth_role",
        AsyncMock(return_value="platform_owner"),
    )
    sess = await open_vertical_entry(msg, "auto", state=None)
    assert sess.active_vertical == "auto"
    assert sess.active_persona is None
    assert msg.answer.await_count >= 1
    text = msg.answer.await_args_list[0].args[0]
    assert "AUTO" in text or "Auto" in text or "Как хотите" in text
    assert "Hercules" not in text


@pytest.mark.asyncio
async def test_beauty_then_auto_sets_auto(monkeypatch):
    uid = 4605100
    vertical_role_registry.clear_vertical(uid)
    context_memory.update(str(uid), vertical="beauty")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    monkeypatch.setattr(
        "services.vertical_nav_service._resolve_auth_role",
        AsyncMock(return_value="platform_owner"),
    )
    await open_vertical_entry(msg, "beauty", state=None)
    assert vertical_role_registry.get(uid).active_vertical == "beauty"
    await open_vertical_entry(msg, "auto", state=None)
    assert vertical_role_registry.get(uid).active_vertical == "auto"
    assert context_memory.get(str(uid)).get("vertical") == "auto"


@pytest.mark.asyncio
async def test_enter_auto_dealer_uses_real_menu(monkeypatch):
    uid = 4605101
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()

    async def _fake_enter_auto(message, user_id, persona):
        from keyboards import auto_vertical_menu

        await message.answer("🚗 Auto · Dealer", reply_markup=auto_vertical_menu())

    monkeypatch.setattr("services.vertical_nav_service._enter_auto", _fake_enter_auto)
    await enter_persona_home(msg, "dealer")
    assert vertical_role_registry.get(uid).active_persona == "dealer"
    assert vertical_role_registry.get(uid).authenticated_role == "platform_owner"


def test_vertical_is_workspace_not_ai_intent():
    """Opening a vertical must not push Concierge / Studio as the only path."""
    from services.telegram_ai_super_app.keyboards import main_menu_keyboard
    from services.vertical_nav_service import FORBIDDEN_VERTICAL_NAV_PHRASES
    from keyboards import travel_module_menu, cafe_beauty_module_menu, agro_menu

    labels = {b.text for row in main_menu_keyboard().keyboard for b in row}
    assert "🚗 Авто" in labels
    assert "🌾 Агро" in labels
    assert "💄 Красота" in labels
    assert "💰 Crypto OTC" in labels
    assert "✈ Travel" in labels
    # Optional AI present but not exclusive
    assert "🤖 AI Консьерж" in labels
    assert "🎨 Студия AI" in labels

    travel_labels = {b.text for row in travel_module_menu().keyboard for b in row}
    assert "🗺 Туры" in travel_labels
    assert "📅 Бронирования" in travel_labels
    assert not any("Студия" in t for t in travel_labels)

    beauty_labels = {b.text for row in cafe_beauty_module_menu().keyboard for b in row}
    assert "☕ Cafe" in beauty_labels
    assert "💄 Салон" in beauty_labels or "💄 Beauty" in beauty_labels

    agro_labels = {b.text for row in agro_menu().keyboard for b in row}
    assert "🌾 Товары" in agro_labels
    assert FORBIDDEN_VERTICAL_NAV_PHRASES  # non-empty guard list


@pytest.mark.asyncio
async def test_crypto_legal_persona_menus(monkeypatch):
    uid = 4605300
    monkeypatch.setattr(
        "services.crypto_auth.CryptoAuthService.can_access_crypto",
        staticmethod(lambda _uid: True),
    )
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")

    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()

    vertical_role_registry.begin_vertical(uid, "crypto")
    await enter_persona_home(msg, "client")
    assert vertical_role_registry.get(uid).active_persona == "client"
    markups = [c.kwargs.get("reply_markup") for c in msg.answer.await_args_list if c.kwargs.get("reply_markup")]
    assert markups
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "🟢 Buy USDT" in texts
    assert "🤖 Crypto Agent" not in texts

    msg.answer.reset_mock()
    vertical_role_registry.begin_vertical(uid, "legal")
    await enter_persona_home(msg, "lawyer")
    assert vertical_role_registry.get(uid).authenticated_role == "platform_owner"
    assert vertical_role_registry.get(uid).active_persona == "lawyer"
    markups = [c.kwargs.get("reply_markup") for c in msg.answer.await_args_list if c.kwargs.get("reply_markup")]
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "📂 Дела" in texts


#
# Sprint 46.6 — navigation stabilization regressions (Beauty/Auto/Agro).
#


@pytest.mark.asyncio
async def test_beauty_owner_menu_is_distinct_from_cafe(monkeypatch):
    """Beauty owner/manager/specialist must not see the Cafe-only button
    or 'Cafe & Beauty' branding — Beauty is its own vertical."""
    uid = 4605400
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "beauty")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()

    for persona in ("owner", "manager", "specialist"):
        msg.answer.reset_mock()
        vertical_role_registry.begin_vertical(uid, "beauty")
        await enter_persona_home(msg, persona)
        markups = [
            c.kwargs.get("reply_markup")
            for c in msg.answer.await_args_list
            if c.kwargs.get("reply_markup")
        ]
        assert markups
        texts = {b.text for row in markups[-1].keyboard for b in row}
        assert "☕ Cafe" not in texts
        assert "💄 Салон" in texts
        for call in msg.answer.await_args_list:
            text = (call.args[0] if call.args else "") or ""
            assert "Cafe & Beauty" not in text


@pytest.mark.asyncio
async def test_beauty_client_menu_booking_oriented():
    uid = 4605401
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "beauty")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "client")
    markups = [
        c.kwargs.get("reply_markup")
        for c in msg.answer.await_args_list
        if c.kwargs.get("reply_markup")
    ]
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "📅 Записи" in texts
    assert "☕ Cafe" not in texts


@pytest.mark.asyncio
async def test_beauty_stub_screen_keeps_beauty_keyboard():
    """Tapping a not-yet-wired Beauty button must fall back to the Beauty
    keyboard, not silently revert to the Cafe & Beauty one (module_stub_screen
    used to always use MODULE_MENUS['cafe_beauty'] = cafe_beauty_module_menu)."""
    import handlers as h
    from keyboards import beauty_module_menu

    uid = 4605402
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "beauty")
    h.active_module[uid] = "cafe_beauty"
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()

    await h.module_stub_screen(msg)

    beauty_texts = {b.text for row in beauty_module_menu().keyboard for b in row}
    call = msg.answer.await_args
    reply_markup = call.kwargs.get("reply_markup")
    texts = {b.text for row in reply_markup.keyboard for b in row}
    assert texts == beauty_texts
    assert "☕ Cafe" not in texts


def test_beauty_ai_studio_is_separate_from_business_menu():
    """Beauty AI Studio must remain reachable, but as a distinct additional
    capability — not the same button/path as the Beauty business workspace."""
    from services.telegram_ai_super_app.catalog import AI_STUDIO_OPTIONS
    from keyboards import beauty_module_menu

    studio_option = next((o for o in AI_STUDIO_OPTIONS if o.id == "beauty"), None)
    assert studio_option is not None
    assert studio_option.vertical == "beauty"

    business_texts = {b.text for row in beauty_module_menu().keyboard for b in row}
    assert studio_option.label not in business_texts


@pytest.mark.asyncio
async def test_auto_owner_hub_exposes_insurance_leasing_credit(monkeypatch):
    """Auto owner must reach insurance/leasing/credit/logistics/legal —
    not just cars — via the real hub menu."""
    monkeypatch.setattr(
        "auto_vertical_handlers.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    )
    monkeypatch.setattr(
        "auto_vertical_handlers.can_access_automotive_ui",
        AsyncMock(return_value=True),
    )
    uid = 4605403
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "auto")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "owner")
    markups = [
        c.kwargs.get("reply_markup")
        for c in msg.answer.await_args_list
        if c.kwargs.get("reply_markup")
    ]
    assert markups
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "🛡 Страхование" in texts
    assert "💳 Лизинг" in texts
    assert "🏦 Кредит" in texts
    assert "🚚 Логистика" in texts


@pytest.mark.asyncio
async def test_auto_client_has_buy_and_sell():
    uid = 4605404
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "auto")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "client")
    markups = [
        c.kwargs.get("reply_markup")
        for c in msg.answer.await_args_list
        if c.kwargs.get("reply_markup")
    ]
    texts = {b.text for row in markups[-1].keyboard for b in row}
    from services.automotive_localization import btn

    assert btn("client_buy_car", "ru") in texts
    assert btn("client_sell_car", "ru") in texts


@pytest.mark.asyncio
async def test_agro_owner_has_buy_sell_marketplace():
    uid = 4605405
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "agro")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "owner")
    markups = [
        c.kwargs.get("reply_markup")
        for c in msg.answer.await_args_list
        if c.kwargs.get("reply_markup")
    ]
    texts = {b.text for row in markups[-1].keyboard for b in row}
    # Buy/sell/marketplace (products+deals+counterparties) — not flattened
    # to farm-ops, which this vertical does not implement in the bot at all.
    assert "🌾 Товары" in texts
    assert "👥 Контрагенты" in texts
    assert "📑 Сделки" in texts


@pytest.mark.asyncio
async def test_agro_client_has_buy_oriented_menu():
    uid = 4605406
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "agro")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "client")
    markups = [
        c.kwargs.get("reply_markup")
        for c in msg.answer.await_args_list
        if c.kwargs.get("reply_markup")
    ]
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "🌾 Товары" in texts


@pytest.mark.asyncio
async def test_switching_beauty_auto_agro_crypto_is_deterministic(monkeypatch):
    """Repeated switching must not leak state between verticals."""
    uid = 4605407
    monkeypatch.setattr(
        "services.crypto_auth.CryptoAuthService.can_access_crypto",
        staticmethod(lambda _uid: True),
    )
    monkeypatch.setattr(
        "auto_vertical_handlers.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    )
    monkeypatch.setattr(
        "auto_vertical_handlers.can_access_automotive_ui",
        AsyncMock(return_value=True),
    )
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()

    sequence = [
        ("beauty", "owner", "💄 Салон"),
        ("auto", "owner", "🛡 Страхование"),
        ("agro", "owner", "🌾 Товары"),
        ("crypto", "owner", "🟢 Buy USDT"),
    ]
    for vertical, persona, expected_text in sequence:
        msg.answer.reset_mock()
        vertical_role_registry.begin_vertical(uid, vertical)
        await enter_persona_home(msg, persona)
        sess = vertical_role_registry.get(uid)
        assert sess.active_vertical == vertical
        assert sess.active_persona == persona
        assert sess.authenticated_role == "platform_owner"
        markups = [
            c.kwargs.get("reply_markup")
            for c in msg.answer.await_args_list
            if c.kwargs.get("reply_markup")
        ]
        assert markups
        texts = {b.text for row in markups[-1].keyboard for b in row}
        assert expected_text in texts


def test_unknown_vertical_fails_safely():
    assert vertical_role_registry.personas_for("does_not_exist") == ("owner", "client")


@pytest.mark.asyncio
async def test_unknown_persona_rejected_without_crash():
    uid = 4605408
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "beauty")
    with pytest.raises(ValueError):
        vertical_role_registry.set_persona(uid, "not_a_real_persona")


@pytest.mark.asyncio
async def test_main_menu_clears_vertical_state():
    from services.vertical_nav_service import go_main_menu

    uid = 4605409
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.begin_vertical(uid, "beauty")
    vertical_role_registry.set_persona(uid, "owner")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await go_main_menu(msg, state=None)
    sess = vertical_role_registry.get(uid)
    assert sess.active_vertical is None
    assert sess.active_persona is None
    assert sess.fsm_state == "platform_home"


@pytest.mark.asyncio
async def test_travel_entry_has_functional_menu(monkeypatch):
    uid = 4605200
    vertical_role_registry.clear_vertical(uid)
    vertical_role_registry.ensure_authenticated_role(uid, "platform_owner")
    vertical_role_registry.begin_vertical(uid, "travel")
    msg = MagicMock()
    msg.from_user = MagicMock(id=uid)
    msg.answer = AsyncMock()
    await enter_persona_home(msg, "owner")
    assert vertical_role_registry.get(uid).active_persona == "owner"
    from services.vertical_nav_service import FORBIDDEN_VERTICAL_NAV_PHRASES

    for call in msg.answer.await_args_list:
        text = (call.args[0] if call.args else "") or ""
        low = text.lower()
        for phrase in FORBIDDEN_VERTICAL_NAV_PHRASES:
            assert phrase not in low, text
    markups = [c.kwargs.get("reply_markup") for c in msg.answer.await_args_list if c.kwargs.get("reply_markup")]
    assert markups
    texts = {b.text for row in markups[-1].keyboard for b in row}
    assert "🗺 Туры" in texts
