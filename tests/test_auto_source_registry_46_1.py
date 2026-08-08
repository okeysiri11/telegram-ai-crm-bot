"""Sprint 46.1 — Source Registry + parallel Auto Search orchestrator tests."""

from __future__ import annotations

import pytest

from services.auto_client_output import format_car_card_ru
from services.auto_conversation_engine import auto_conversation_engine
from services.auto_localization_gate import scan_user_facing_strings
from services.auto_request_memory import auto_request_memory, parse_search_utterance
from services.auto_search_orchestrator import auto_search_orchestrator
from services.auto_source_registry import auto_source_registry


@pytest.fixture(autouse=True)
def _clean():
    auto_request_memory.clear()
    auto_source_registry.reset_builtins()
    yield
    auto_request_memory.clear()


def test_builtin_telegram_sources_registered_and_enabled():
    ids = {s.id for s in auto_source_registry.list_all()}
    assert "tg_keepcar" in ids
    assert "tg_isauto99" in ids
    assert "tg_kievavto" in ids
    assert "tg_avtosale_odessa777" in ids
    assert "tg_imperiya_auto" in ids
    keep = auto_source_registry.get("tg_keepcar")
    assert keep is not None
    assert keep.enabled is True
    assert keep.source_url == "https://t.me/keepcar"
    assert keep.name == "KEEP CAR"
    assert keep.source_type == "telegram_channel"
    isauto = auto_source_registry.get("tg_isauto99")
    assert isauto and isauto.source_url == "https://t.me/isAuto99"
    kiev = auto_source_registry.get("tg_kievavto")
    assert kiev and kiev.source_url == "https://t.me/KievavtoLocation"
    odessa = auto_source_registry.get("tg_avtosale_odessa777")
    assert odessa is not None
    assert odessa.source_url == "https://t.me/avtosale_odessa777"
    assert odessa.name == "avto_batya777"
    assert odessa.metadata.get("resolved_name") == "avto_batya777"
    assert odessa.region == "Odessa / Ukraine"
    assert odessa.searchable is True
    imperiya = auto_source_registry.get("tg_imperiya_auto")
    assert imperiya is not None
    assert imperiya.source_url == "https://t.me/imperiya_auto"
    assert "Imperiya" in imperiya.name or "Імперія" in imperiya.name
    assert imperiya.region == "Ukraine"
    assert imperiya.searchable is True


def test_telegram_pool_has_five_channels():
    urls = set(auto_source_registry.telegram_pool_urls())
    assert urls == {
        "https://t.me/keepcar",
        "https://t.me/isAuto99",
        "https://t.me/KievavtoLocation",
        "https://t.me/avtosale_odessa777",
        "https://t.me/imperiya_auto",
    }
    assert len(auto_source_registry.list_telegram_channels()) == 5


def test_public_web_sources_not_replaced():
    ids = {s.id for s in auto_source_registry.list_enabled()}
    assert "web_autoria" in ids
    assert "web_olx_auto" in ids
    assert "web_rst" in ids
    assert "dealer_warehouse" in ids


def test_telegram_requires_configuration_status():
    for sid in (
        "tg_keepcar",
        "tg_isauto99",
        "tg_kievavto",
        "tg_avtosale_odessa777",
        "tg_imperiya_auto",
    ):
        s = auto_source_registry.get(sid)
        assert s is not None
        assert s.status == "requires_configuration"
        assert s.searchable is True
    probe = auto_source_registry.probe("tg_keepcar")
    assert probe["ok"] is False
    assert "настрой" in probe["message_ru"].lower()


@pytest.mark.asyncio
async def test_parallel_search_queries_all_five_telegram_plus_web():
    slots = parse_search_utterance("BMW X5 Одесса до 15000$")
    result = await auto_search_orchestrator.search(slots, user_id=1, mode="fast")
    for sid in (
        "tg_keepcar",
        "tg_isauto99",
        "tg_kievavto",
        "tg_avtosale_odessa777",
        "tg_imperiya_auto",
        "web_autoria",
        "web_olx_auto",
        "web_rst",
        "dealer_warehouse",
    ):
        assert sid in result["sources_queried"]
    assert result["statuses"]["tg_avtosale_odessa777"] == "requires_configuration"
    assert result["statuses"]["tg_imperiya_auto"] == "requires_configuration"
    assert result["listings"], "public web / warehouse must still return cars"
    assert all("source" in c for c in result["listings"])
    assert all("listing_url" in c for c in result["listings"])
    assert all("external_id" in c for c in result["listings"])


@pytest.mark.asyncio
async def test_unified_telegram_adapter_normalizes_cached_posts():
    from services.auto_search_adapters import TelegramChannelAdapter, normalize_telegram_post

    src = auto_source_registry.get("tg_avtosale_odessa777")
    assert src is not None
    src.metadata = {
        **(src.metadata or {}),
        "bot_can_read": True,
        "cached_posts": [
            {
                "message_id": 42,
                "text": "BMW X5 2017 дизель 184000 км цена $14800 Одесса",
                "photos": ["https://example.com/x5.jpg"],
                "published_at": "2026-08-01T10:00:00+00:00",
            }
        ],
    }
    auto_source_registry._sources[src.id] = src
    items, status = await TelegramChannelAdapter().search(
        src,
        parse_search_utterance("BMW X5 Одесса до 15000$"),
        user_id=1,
    )
    assert status == "active"
    assert len(items) == 1
    assert items[0].make == "BMW"
    assert items[0].model == "X5"
    assert items[0].year == 2017
    assert items[0].price == 14800
    assert items[0].fuel == "дизель"
    assert items[0].photos
    assert "t.me/avtosale_odessa777/42" in items[0].listing_url
    assert items[0].published_at

    other = auto_source_registry.get("tg_imperiya_auto")
    listing = normalize_telegram_post(
        other,
        {"message_id": 7, "text": "BMW X5 до 14000$ Киев бензин"},
    )
    assert listing is not None
    assert listing.source == other.name
    assert listing.make == "BMW"


@pytest.mark.asyncio
async def test_priority_ranks_but_does_not_exclude():
    slots = parse_search_utterance("BMW X5 до 15000")
    result = await auto_search_orchestrator.search(slots, user_id=2, mode="deep")
    sources_in_results = {c["source"] for c in result["listings"]}
    # At least one public web brand name present among results
    assert sources_in_results
    assert len(result["sources_queried"]) >= 5


@pytest.mark.asyncio
async def test_query_bmw_x5_odessa_15000_dollars_no_questionnaire():
    uid = 461200
    r = await auto_conversation_engine.handle(
        uid,
        "BMW X5 Одесса до 15000 долларов",
        role="client",
    )
    assert r["started_search"] is True
    assert "Ищу" in r["reply_ru"]
    assert len(r["cars"]) >= 1
    assert "Score" not in r["reply_ru"]
    card = format_car_card_ru(r["cars"][0])
    assert "🚗" in card
    assert "📅" in card
    assert "💰" in card
    assert "adapter" not in card.lower()
    assert "parser" not in card.lower()
    assert "tg_keepcar" not in card


def test_owner_can_add_sources_and_toggle():
    added = auto_source_registry.add_telegram_channel(
        name="My Channel",
        url="https://t.me/mycars",
        source_id="tg_owner_test",
    )
    assert added.enabled
    assert added.category == "telegram"
    auto_source_registry.set_enabled("tg_owner_test", False)
    assert auto_source_registry.get("tg_owner_test").enabled is False
    web = auto_source_registry.add_web_source(
        name="Extra Cars",
        url="https://example.com/cars",
        source_id="web_owner_test",
    )
    assert web.source_type == "public_web"
    assert "Моя база" in auto_source_registry.menu_text_ru()
    assert "Telegram-каналы" in auto_source_registry.menu_text_ru()


@pytest.mark.asyncio
async def test_listing_schema_fields():
    slots = parse_search_utterance("BMW X5")
    from services.auto_search_adapters import PublicWebAdapter

    src = auto_source_registry.get("web_autoria")
    items, status = await PublicWebAdapter().search(src, slots, user_id=1)
    assert status == "active"
    assert items
    d = items[0].to_dict()
    for key in (
        "source",
        "source_type",
        "source_url",
        "listing_url",
        "external_id",
        "make",
        "model",
        "year",
        "price",
        "currency",
        "mileage",
        "fuel",
        "transmission",
        "location",
        "description",
        "photos",
        "published_at",
        "fetched_at",
    ):
        assert key in d


def test_localization_gate_still_clean():
    hard = [v for v in scan_user_facing_strings(locale="ru") if str(v["reason"]).startswith("forbidden")]
    assert hard == []
