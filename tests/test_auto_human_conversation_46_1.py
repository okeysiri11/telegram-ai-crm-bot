"""Sprint 46.1 — Human conversation, VIN state, refine regression tests."""

from __future__ import annotations

import pytest

from services.auto_client_flow_engine import SKIP_TOKENS, YES_TOKENS
from services.auto_client_output import sanitize_ai_reply_for_client
from services.auto_conversation_engine import auto_conversation_engine
from services.auto_conversation_quality_guard import apply_conversation_quality_guard
from services.auto_dialog_state import (
    VIN_CHOICE,
    VIN_SKIPPED,
    WAITING_FOR_VIN,
    auto_dialog_state,
)
from services.auto_human_conversation_policy import DEFAULT_AI_STYLE, resolve_ai_style
from services.auto_localization_gate import scan_user_facing_strings
from services.auto_request_memory import auto_request_memory, parse_search_utterance


@pytest.fixture(autouse=True)
def _clean():
    auto_request_memory.clear()
    auto_dialog_state.clear()
    yield
    auto_request_memory.clear()
    auto_dialog_state.clear()


# --- TEST 1–3 VIN ---


def test_vin_net_skips_and_continues():
    uid = 461301
    auto_dialog_state.begin_vin_choice(uid)
    t = auto_dialog_state.resolve_short_answer(uid, "Нет")
    assert t is not None
    assert t["event"] == VIN_SKIPPED
    assert t["continue_workflow"] is True
    assert t["vin"] is None
    assert "без VIN" in (t["reply_ru"] or "")
    assert auto_dialog_state.get(uid).vin_status == VIN_SKIPPED


def test_vin_2_same_as_net():
    uid = 461302
    auto_dialog_state.begin_vin_choice(uid)
    t = auto_dialog_state.resolve_short_answer(uid, "2")
    assert t is not None
    assert t["event"] == VIN_SKIPPED
    assert t["continue_workflow"] is True


def test_vin_da_waits_for_vin_only():
    uid = 461303
    auto_dialog_state.begin_vin_choice(uid)
    t = auto_dialog_state.resolve_short_answer(uid, "Да")
    assert t is not None
    assert t["event"] == WAITING_FOR_VIN
    assert t["ask_vin_only"] is True
    assert "VIN" in (t["reply_ru"] or "")
    assert auto_dialog_state.get(uid).phase != VIN_CHOICE


def test_skip_and_yes_tokens_cover_buttons_and_text():
    assert "нет" in SKIP_TOKENS
    assert "2" in SKIP_TOKENS
    assert "да" in YES_TOKENS
    assert "1" in YES_TOKENS


# --- TEST 4 search immediate ---


@pytest.mark.asyncio
async def test_bmw_x5_odessa_budget_searches_immediately():
    uid = 461304
    r = await auto_conversation_engine.handle(uid, "BMW X5 Одесса до $15000")
    assert r["started_search"] is True
    assert "Ищу" in r["reply_ru"]
    assert "какую марку" not in r["reply_ru"].lower()
    assert "Score" not in r["reply_ru"]


# --- TEST 5 leasing ---


@pytest.mark.asyncio
async def test_leasing_full_line_starts_workflow():
    uid = 461305
    await auto_conversation_engine.handle(uid, "Лизинг")
    r = await auto_conversation_engine.handle(
        uid,
        "BMW X5 б/у, на год, взнос $2000, Одесса. Тимофей 0638917326",
    )
    assert r.get("intent") == "LEASING"
    assert r["started_search"] is True
    slots = r["slots"]
    assert slots["brand"] == "BMW"
    assert slots["model"] == "X5"
    assert slots["city"] == "Одесса"
    assert slots.get("down_payment") == 2000
    assert slots.get("client_name") == "Тимофей"
    assert slots.get("client_phone")
    assert "Правильно ли я понял" not in r["reply_ru"]
    assert "физическое или юридическое" not in r["reply_ru"].lower()


@pytest.mark.asyncio
async def test_leasing_standalone_line_intent():
    uid = 461306
    r = await auto_conversation_engine.handle(
        uid,
        "BMW X5 б/у на год взнос $2000 Одесса Тимофей 0638917326",
    )
    assert r.get("intent") == "LEASING"
    assert r["started_search"] is True


# --- TEST 6 no cross-sell ---


@pytest.mark.asyncio
async def test_leasing_closing_no_cross_sell():
    uid = 461307
    r = await auto_conversation_engine.handle(
        uid,
        "BMW X5 б/у на год взнос $2000 Одесса Тимофей 0638917326",
    )
    low = r["reply_ru"].lower()
    assert "аренда" not in low
    assert "страховк" not in low
    assert "кредит" not in low
    assert "Посмотрите" in r["reply_ru"] or "вариантов" in low


# --- TEST 7 no CRM meta ---


def test_client_response_strips_score_priority():
    raw = "Нашёл авто\nScore: 75\nPriority: HIGH\nDept: Sales\nIntent: BUY_CAR"
    out = sanitize_ai_reply_for_client(raw, role="client")
    assert "Score" not in out
    assert "Priority" not in out
    assert "Intent" not in out


# --- TEST 8 diesel refine ---


@pytest.mark.asyncio
async def test_diesel_refine_preserves_context():
    uid = 461308
    await auto_conversation_engine.handle(uid, "BMW X5 до $15000")
    r = await auto_conversation_engine.handle(uid, "только дизель")
    assert r["started_search"] is True
    assert r["slots"]["brand"] == "BMW"
    assert r["slots"]["budget_max"] == 15000
    assert r["slots"]["fuel"] == "diesel"


@pytest.mark.asyncio
async def test_budget_raise_mozno_do():
    uid = 461309
    await auto_conversation_engine.handle(uid, "BMW X5 до $15000")
    r = await auto_conversation_engine.handle(uid, "Можно до $17000")
    assert r["slots"]["budget_max"] == 17000
    assert r["slots"]["brand"] == "BMW"
    assert r["started_search"] is True
    assert "какой бюджет" not in r["reply_ru"].lower()


# --- TEST 9 Russian First ---


@pytest.mark.asyncio
async def test_russian_conversation_no_english():
    uid = 461310
    r = await auto_conversation_engine.handle(uid, "BMW X5 Одесса до 15000")
    # Brand model codes OK; no English sentences
    assert "Please" not in r["reply_ru"]
    assert "Did I understand" not in r["reply_ru"]
    assert "Score" not in r["reply_ru"]
    hard = [v for v in scan_user_facing_strings(locale="ru") if str(v["reason"]).startswith("forbidden")]
    assert hard == []


def test_quality_guard_rewrites_bad_reply():
    bad = (
        "Правильно ли я понял ваш запрос? Укажите год/пробег/комплектацию. "
        "Нужна ли аренда? Score: 10"
    )
    out = apply_conversation_quality_guard(
        bad,
        known={"brand": "BMW", "budget_max": 15000, "intent": "BUY_CAR"},
        settings=DEFAULT_AI_STYLE,
    )
    assert "Правильно ли я понял" not in out
    assert "Score" not in out
    assert "аренда" not in out.lower()


def test_ai_style_defaults_auto():
    st = resolve_ai_style({})
    assert st["conversation_style"] == "concise"
    assert st["ask_optional_questions"] is False
    assert st["cross_sell"] is False
    assert st["human_conversation_guard"] is True
    assert st["max_clarifying_questions"] == 1


def test_parse_budget_mozno_do():
    base = parse_search_utterance("BMW X5 до $15000")
    refined = parse_search_utterance("Можно до $17000", base=base)
    assert refined.budget_max == 17000
    assert refined.brand == "BMW"
