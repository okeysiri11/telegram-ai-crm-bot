"""Tests — Creative Factory (Sprint 36.9)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_ai.creative_router import register_creative_factory_routes
from platform_ai.creative_service import creative_factory_service as cfs
from platform_management.permissions import ManagementRole


@pytest.fixture
def engine():
    cfs.reset()
    cfs.ensure_ready()
    yield cfs
    cfs.reset()


@pytest.mark.asyncio
async def test_studio_generation_types(engine):
    types = [
        "landing_page",
        "advertisement",
        "social_post",
        "blog_article",
        "email_campaign",
        "sales_proposal",
        "commercial_offer",
        "presentation",
        "pdf_document",
        "marketing_report",
    ]
    for ctype in types:
        asset = await engine.generate({"creative_type": ctype, "topic": f"demo {ctype}", "modality": "text"})
        assert asset["creative_type"] == ctype
        assert asset["content"]
        assert asset["provider_id"]
    assert engine.statistics()["generations"] >= 10


@pytest.mark.asyncio
async def test_media_providers_failover(engine):
    providers = engine.list_providers()
    modalities = {p["modality"] for p in providers}
    assert modalities >= {
        "text",
        "image",
        "video",
        "voice",
        "speech_to_text",
        "text_to_speech",
    }

    engine.engine.media.set_available("openai_text", False)
    out = await engine.media_generate({"modality": "text", "prompt": "hello", "provider_id": "openai_text"})
    assert out["provider_id"] != "openai_text"
    assert out["failover_used"] is True


@pytest.mark.asyncio
async def test_campaign_brand_library_publish(engine):
    brands = engine.list_brands()
    assert any(b["brand_id"] == "brand_ados" for b in brands)
    assert brands[0]["colors"]
    assert brands[0]["typography"]
    assert brands[0]["tone_of_voice"]

    asset = await engine.generate(
        {"creative_type": "social_post", "topic": "brand launch", "brand_id": "brand_ados"}
    )
    camp = engine.create_campaign(
        {
            "name": "Launch",
            "objective": "awareness",
            "audience": "executives",
            "channels": ["telegram", "linkedin", "x"],
            "budget": 2500,
            "creative_ids": [asset["asset_id"]],
        }
    )
    assert camp["campaign_id"]
    attached = engine.attach_creative(camp["campaign_id"], asset["asset_id"])
    assert asset["asset_id"] in attached["creative_ids"]

    analytics = engine.campaign_analytics(camp["campaign_id"])
    assert "impressions" in analytics["analytics"]

    media = engine.list_media()
    assert len(media) >= 1
    hits = engine.search("brand launch")
    assert hits

    reviewed = engine.review_asset(asset["asset_id"], {"approve": True})
    assert reviewed["status"] == "approved"
    versioned = engine.version_asset(asset["asset_id"], {"content": "v2 body"})
    assert versioned["version"] == 2

    job = await engine.publish({"asset_id": asset["asset_id"], "channel": "telegram"})
    assert job["status"] == "published"
    assert job["external_id"]

    # scheduled
    import time

    asset2 = await engine.generate({"creative_type": "advertisement", "topic": "later"})
    scheduled = await engine.publish(
        {"asset_id": asset2["asset_id"], "channel": "linkedin", "scheduled_at": time.time() + 3600}
    )
    assert scheduled["status"] == "scheduled"
    # force due
    engine.engine.publish_jobs[scheduled["job_id"]].scheduled_at = time.time() - 1
    done = engine.run_scheduled()
    assert done


@pytest.mark.asyncio
async def test_integrations(engine):
    from platform_service_builder.service import service_builder

    service_builder.reset()
    service_builder.ensure_seed()

    ai = await engine.for_ai_runtime({})
    assert ai["consumer"] == "ai_runtime"
    assert ai["asset"]["asset_id"]

    ma = await engine.for_multi_agent({})
    assert ma["consumer"] == "multi_agent_runtime"

    mem = await engine.for_project_memory({})
    assert mem["consumer"] == "project_memory"

    ctx = await engine.for_context_engine({})
    assert ctx["consumer"] == "context_engine"

    wf = await engine.for_workflow({})
    assert wf["consumer"] == "workflow"
    assert wf["campaign"]["campaign_id"]

    eb = await engine.for_event_bus({})
    assert eb["consumer"] == "event_bus"
    assert eb["event"]["type"] == "creative.generated"

    voice = await engine.for_voice({"transcript": "create social post about launch"})
    assert voice["consumer"] == "voice_runtime"

    skills = await engine.for_skills_sdk({})
    assert skills["consumer"] == "skills_sdk"

    svc = service_builder.get("svc_creative_factory")
    assert svc.id == "svc_creative_factory"
    assert svc.manifest.name == "creative_factory"
    assert "/api/creative" in svc.manifest.api
    service_builder.reset()


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_creative_factory_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/creative/status", headers=auth_headers)
            assert res.status == 200
            body = await res.json()
            assert body["data"]["sprint"] == "36.9"

            res = await client.post(
                "/api/creative/generate",
                headers=auth_headers,
                json={"creative_type": "blog_article", "topic": "API demo"},
            )
            assert res.status == 201
            asset = (await res.json())["data"]
            assert asset["asset_id"]

            res = await client.get("/api/campaigns", headers=auth_headers)
            assert res.status == 200

            res = await client.post(
                "/api/campaigns",
                headers=auth_headers,
                json={"name": "API Camp", "channels": ["telegram"], "creative_ids": [asset["asset_id"]]},
            )
            assert res.status == 201

            res = await client.get("/api/media", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

            res = await client.post(
                "/api/media/generate",
                headers=auth_headers,
                json={"modality": "image", "prompt": "hero visual"},
            )
            assert res.status == 201

            res = await client.post(
                "/api/creative/publish",
                headers=auth_headers,
                json={"asset_id": asset["asset_id"], "channel": "x"},
            )
            assert res.status == 201

            res = await client.get("/management/v1/creative/status", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["service"] == "creative_factory"

    cfs.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/creative-console/CreativeFactoryPage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Creative Dashboard",
        "Campaign Builder",
        "Brand Center",
        "Media Library",
        "Prompt Studio",
        "Publishing Hub",
        "Analytics",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.creative_factory import (
        BrandProfileRow,
        CampaignChannelRow,
        CampaignRow,
        CreativeAssetRow,
        CreativeHistoryRow,
        CreativeProjectRow,
        CreativeTemplateRow,
        MediaLibraryRow,
    )

    assert CreativeProjectRow.__tablename__ == "creative_projects"
    assert CreativeAssetRow.__tablename__ == "creative_assets"
    assert CreativeTemplateRow.__tablename__ == "creative_templates"
    assert CampaignRow.__tablename__ == "campaigns"
    assert CampaignChannelRow.__tablename__ == "campaign_channels"
    assert MediaLibraryRow.__tablename__ == "media_library"
    assert BrandProfileRow.__tablename__ == "brand_profiles"
    assert CreativeHistoryRow.__tablename__ == "creative_history"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/s2m345678901_creative_factory_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "creative_projects",
        "creative_assets",
        "creative_templates",
        "campaigns",
        "campaign_channels",
        "media_library",
        "brand_profiles",
        "creative_history",
    ):
        assert table in text
    assert 'revision: str = "s2m345678901"' in text
    assert 'down_revision: Union[str, None] = "r1l234567890"' in text


def test_exports():
    from platform_ai import creative_factory_engine, creative_factory_service

    assert creative_factory_engine and creative_factory_service


def test_docs_present():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/CREATIVE_FACTORY.md").is_file()
    assert (root / "docs/SPRINT_36_9_RESULT.md").is_file()
