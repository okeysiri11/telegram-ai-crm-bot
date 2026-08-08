"""Sprint 46.1 — Auto Telegram conversation-first AI manager tests."""

from __future__ import annotations

import pytest

from services.auto_client_output import (
    format_car_card_ru,
    sanitize_ai_reply_for_client,
    user_facing_rates_missing_ru,
    user_facing_tenant_error_ru,
)
from services.auto_conversation_engine import auto_conversation_engine
from services.auto_dealer_settings import DEALER_SETTINGS_SECTIONS, plan_label_ru
from services.auto_localization_gate import FORBIDDEN_PHRASES, scan_user_facing_strings
from services.auto_request_memory import auto_request_memory, conversation_summary_ru, parse_search_utterance
from services.auto_saved_search import auto_saved_search
from services.automotive_localization import t


@pytest.fixture(autouse=True)
def _clean_memory():
    auto_request_memory.clear()
    yield
    auto_request_memory.clear()


def test_parse_bmw_x5_odessa_budget():
    slots = parse_search_utterance("BMW X5 Одесса до $15000")
    assert slots.brand == "BMW"
    assert slots.model == "X5"
    assert slots.city == "Одесса"
    assert slots.budget_max == 15000


def test_refine_keeps_brand_city_budget_adds_diesel():
    base = parse_search_utterance("BMW X5 Одесса до $15000")
    refined = parse_search_utterance("только дизель", base=base)
    assert refined.brand == "BMW"
    assert refined.model == "X5"
    assert refined.city == "Одесса"
    assert refined.budget_max == 15000
    assert refined.fuel == "diesel"


def test_year_and_cheaper_and_city_only():
    base = parse_search_utterance("BMW X5 до 15000")
    y = parse_search_utterance("2016+", base=base)
    assert y.year_min == 2016
    cheap = parse_search_utterance("дешевле", base=y)
    assert cheap.budget_max == 15000 * 0.9
    city = parse_search_utterance("только Одесса", base=cheap)
    assert city.city == "Одесса"


def test_find_x5_without_brand():
    slots = parse_search_utterance("Найди X5")
    assert slots.model == "X5"
    assert slots.brand == "BMW"


@pytest.mark.asyncio
async def test_acceptance_search_then_diesel_refine():
    uid = 461001
    r1 = await auto_conversation_engine.handle(uid, "Найди BMW X5 в Одессе до 15000$ и пришли сюда.")
    assert r1["started_search"] is True
    assert "Ищу" in r1["reply_ru"]
    assert "BMW" in r1["reply_ru"]
    assert "Score" not in r1["reply_ru"]
    assert "Intent" not in r1["reply_ru"]
    cars1 = r1["cars"]
    assert len(cars1) >= 1

    r2 = await auto_conversation_engine.handle(uid, "Только дизель.")
    assert r2["started_search"] is True
    slots = r2["slots"]
    assert slots["brand"] == "BMW"
    assert slots["fuel"] == "diesel"
    assert slots["budget_max"] == 15000
    assert all(
        "диз" in str(c.get("fuel", "")).lower() or "diesel" in str(c.get("fuel", "")).lower()
        for c in r2["cars"]
    )


@pytest.mark.asyncio
async def test_compare_and_save_favorite():
    uid = 461002
    await auto_conversation_engine.handle(uid, "BMW X5 Одесса до 15000")
    cmp = await auto_conversation_engine.handle(uid, "первые две сравни")
    assert "Сравнение" in cmp["reply_ru"]
    save = await auto_conversation_engine.handle(uid, "вторую сохрани")
    assert "избранное" in save["reply_ru"].lower()


@pytest.mark.asyncio
async def test_single_lead_per_dialog():
    uid = 461003
    a = await auto_conversation_engine.handle(uid, "Найди BMW X5")
    b = await auto_conversation_engine.handle(uid, "только дизель")
    assert a.get("lead_id")
    assert b.get("lead_id") == a.get("lead_id")


@pytest.mark.asyncio
async def test_monitor_saved_search():
    uid = 461004
    await auto_conversation_engine.handle(uid, "BMW X5 Одесса до 15000")
    mon = await auto_conversation_engine.handle(uid, "следить")
    assert "Слежу" in mon["reply_ru"] or "🔔" in mon["reply_ru"]
    assert auto_saved_search.list_for(uid)


def test_client_sanitizer_strips_internal_meta():
    raw = "Нашёл авто\n\nScore: 75\nPriority: MEDIUM\nDept: Sales\nIntent: BUY_CAR"
    out = sanitize_ai_reply_for_client(raw, role="client")
    assert "Score" not in out
    assert "Priority" not in out
    assert "Intent" not in out
    assert "Нашёл" in out


def test_tenant_and_rates_user_messages_ru():
    assert "организац" in user_facing_tenant_error_ru().lower()
    assert "No active tenant" not in user_facing_tenant_error_ru()
    assert "Курсы дилера" in user_facing_rates_missing_ru(is_owner=True)
    assert user_facing_rates_missing_ru(is_owner=False) == ""


def test_plan_labels_ru_ids_en():
    assert plan_label_ru("starter") == "Старт"
    assert plan_label_ru("pro") == "Профессиональный"
    assert plan_label_ru("business") == "Бизнес"
    assert plan_label_ru("enterprise") == "Корпоративный"
    assert plan_label_ru("STARTER") == "Старт"


def test_dealer_settings_sections():
    titles = [t for _, t in DEALER_SETTINGS_SECTIONS]
    for need in (
        "Источники поиска",
        "Курсы",
        "Комиссии",
        "Тарифы",
        "Услуги",
        "Контакты",
        "Города",
        "Бренды",
        "Telegram-каналы",
        "Партнёры",
        "Склад",
        "Правила AI",
    ):
        assert need in titles


def test_car_card_ru_no_english_labels():
    card = format_car_card_ru(
        {
            "title": "BMW X5",
            "year": 2018,
            "price": 14000,
            "fuel": "дизель",
            "city": "Одесса",
            "mileage": 90000,
            "url": "https://example.com/1",
        }
    )
    assert "📅" in card
    assert "💰" in card
    assert "Mileage:" not in card
    assert "Color:" not in card


def test_conversation_summary_ru():
    slots = parse_search_utterance("BMW X5 Одесса до 15000")
    summary = conversation_summary_ru(slots)
    assert "BMW X5" in summary
    assert "Одесс" in summary
    assert "Telegram" in summary


def test_localization_keys():
    assert "Напишите" in t("telegram.auto.ai_welcome", "ru")
    assert "организац" in t("telegram.auto.tenant_missing", "ru").lower()


def test_localization_gate_no_forbidden_leaks():
    violations = scan_user_facing_strings(locale="ru")
    # Filter to high-confidence forbidden phrases only for CI hard fail
    hard = [v for v in violations if str(v["reason"]).startswith("forbidden_phrase:")]
    assert hard == [], hard


def test_forbidden_phrases_cover_sprint_requirements():
    for p in (
        "Dealer rates not configured",
        "No active tenant context",
        "Score:",
        "unlimited channels",
        "STARTER",
    ):
        assert p in FORBIDDEN_PHRASES


@pytest.mark.asyncio
async def test_e2e_dry_run_pipeline():
    """Telegram → Conversation → Memory → Search → Cards (dry-run)."""
    uid = 461099
    # Conversation Manager
    r = await auto_conversation_engine.handle(
        uid,
        "Найди BMW X5 в Одессе до 15000$",
        role="client",
    )
    assert r["started_search"]
    # Memory slots
    mem = auto_request_memory.get(uid)
    assert mem is not None
    assert mem.brand == "BMW"
    assert mem.city == "Одесса"
    # Results → cards
    assert r["cars"]
    card = format_car_card_ru(r["cars"][0])
    assert "BMW" in card or "X5" in card
    assert "Score" not in r["reply_ru"]
    # Follow-up refine without re-qualification
    r2 = await auto_conversation_engine.handle(uid, "только дизель")
    assert r2["slots"]["brand"] == "BMW"
    assert r2["slots"]["budget_max"] == 15000


@pytest.mark.asyncio
async def test_vin_skip_phrases_do_not_block_search():
    uid = 461050
    for phrase in ("пропустить", "не знаю", "нет", "1", "2", "не задавай вопросов, ищи"):
        auto_request_memory.clear(uid)
        r = await auto_conversation_engine.handle(uid, f"BMW X5 {phrase}")
        assert r["started_search"] or "Ищу" in r.get("reply_ru", "") or r.get("cars") is not None
