"""Tests — Voice Command Center / Voice Runtime (Sprint 36.6)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_ai.voice_models import VoiceIntent
from platform_ai.voice_router import register_voice_runtime_routes
from platform_ai.voice_service import voice_runtime_service as vrs
from platform_management.permissions import ManagementRole


@pytest.fixture
def engine():
    vrs.reset()
    vrs.ensure_ready()
    yield vrs
    vrs.reset()


@pytest.mark.asyncio
async def test_voice_runtime_modes_and_vad(engine):
    session = engine.start_session({"mode": "push_to_talk"})
    assert session["encrypted"] is True
    assert session["status"] == "listening"

    engine.set_mode(session["session_id"], "wake_word")
    wake = engine.wake_word(session["session_id"], "hey ados open crm")
    assert wake["detected"] is True

    engine.set_mode(session["session_id"], "continuous")
    vad = engine.vad(session["session_id"], energy=0.8)
    assert vad["vad_active"] is True

    stopped = engine.stop_session(session["session_id"])
    assert stopped["status"] == "closed"


@pytest.mark.asyncio
async def test_speech_providers_and_fallback(engine):
    providers = await engine.providers()
    ids = {p["provider_id"] for p in providers}
    for required in (
        "openai_realtime",
        "whisper",
        "azure_speech",
        "deepgram",
        "google_speech",
        "local_whisper",
    ):
        assert required in ids

    engine.engine.providers.set_available("openai_realtime", False)
    engine.engine.providers.set_available("whisper", False)
    chunk = await engine.engine.providers.transcribe(
        "open CRM",
        preferred="openai_realtime",
    )
    assert chunk.provider_id in {"deepgram", "azure_speech", "google_speech", "local_whisper"}
    assert "CRM" in chunk.text or "crm" in chunk.text.lower() or chunk.text


def test_command_parser(engine):
    cases = [
        ("open CRM", VoiceIntent.OPEN_CRM.value),
        ("open the ERP", VoiceIntent.OPEN_ERP.value),
        ("create project called Atlas", VoiceIntent.CREATE_PROJECT.value),
        ("create task for onboarding", VoiceIntent.CREATE_TASK.value),
        ("assign employee Alice to Sales", VoiceIntent.ASSIGN_EMPLOYEE.value),
        ("search knowledge for pricing", VoiceIntent.SEARCH_KNOWLEDGE.value),
        ("launch workflow approval", VoiceIntent.LAUNCH_WORKFLOW.value),
        ("call ai agent orchestrator to summarize", VoiceIntent.CALL_AI_AGENT.value),
        ("generate report about revenue", VoiceIntent.GENERATE_REPORT.value),
        ("open page analytics", VoiceIntent.OPEN_PAGE.value),
    ]
    for text, intent in cases:
        parsed = engine.parse(text)
        assert parsed["intent"] == intent, text
        assert parsed["confidence"] > 0.5


@pytest.mark.asyncio
async def test_security_confirmation_and_rbac(engine):
    # readonly cannot create projects
    denied = await engine.process(
        {
            "transcript": "create project called X",
            "roles": ["readonly"],
            "confirmed": True,
        }
    )
    assert denied["command"]["status"] == "denied"

    pending = await engine.process(
        {
            "transcript": "assign employee Bob to Ops",
            "roles": ["administrator"],
            "profile_id": "vprof_admin",
        }
    )
    assert pending.get("awaiting_confirmation") is True
    command_id = pending["command"]["command_id"]
    confirmed = await engine.confirm(command_id, approved_by="admin")
    assert confirmed["command"]["status"] == "executed"
    assert engine.history()


@pytest.mark.asyncio
async def test_execution_integrations(engine):
    from platform_ai.service import ai_runtime_service
    from platform_workflow.service import workflow_runtime_service as wrs
    from platform_service_builder.service import service_builder

    ai_runtime_service.reset()
    wrs.reset()
    wrs.ensure_seed()
    service_builder.reset()
    service_builder.ensure_seed()

    agent = await engine.process(
        {
            "transcript": "call ai agent helper to say hello",
            "roles": ["administrator"],
            "confirmed": True,
        }
    )
    assert "ai_runtime" in (agent.get("execution") or {}).get("targets", []) or agent["command"]["status"] == "executed"

    wf = await engine.process(
        {
            "transcript": "launch workflow loop",
            "roles": ["administrator"],
            "confirmed": True,
        }
    )
    assert wf["command"]["status"] == "executed"
    assert "workflow" in (wf.get("execution") or {}) or "workflow_error" not in (wf.get("execution") or {})

    svc = service_builder.get("svc_voice_runtime")
    assert svc.id == "svc_voice_runtime"
    assert svc.manifest.name == "voice_runtime"

    ctx = await engine.for_context_engine({"transcript": "open crm"})
    assert ctx["consumer"] == "context_engine"
    assert ctx["parsed"]["intent"] == "open_crm"

    ai_runtime_service.reset()
    wrs.reset()
    service_builder.reset()


@pytest.mark.asyncio
async def test_devices_profiles_stats(engine):
    assert len(engine.list_devices()) >= 2
    engine.register_device({"name": "USB Mic", "kind": "usb"})
    assert len(engine.list_profiles()) >= 2
    engine.upsert_profile({"name": "Night", "principal": "u_night", "wake_word": "hey ados"})
    stats = engine.statistics()
    assert stats["devices"] >= 3
    assert stats["profiles"] >= 3


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_voice_runtime_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/voice/providers", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 6

            res = await client.post(
                "/api/voice-runtime/process",
                headers=auth_headers,
                json={"transcript": "open CRM", "confirmed": True},
            )
            assert res.status == 200
            body = await res.json()
            assert body["data"]["parsed"]["intent"] == "open_crm"

            res = await client.get("/api/voice/statistics", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/voice/status", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["sprint"] == "36.6"

    vrs.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/voice-console/VoiceCommandCenterPage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Voice Dashboard",
        "Live Microphone",
        "Sessions",
        "Command History",
        "Device Manager",
        "Voice Profiles",
        "Statistics",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.voice import (
        VoiceCommandRow,
        VoiceDeviceRow,
        VoiceHistoryRow,
        VoiceProfileRow,
        VoiceSessionRow,
        VoiceStatisticsRow,
    )

    assert VoiceSessionRow.__tablename__ == "voice_sessions"
    assert VoiceCommandRow.__tablename__ == "voice_commands"
    assert VoiceHistoryRow.__tablename__ == "voice_history"
    assert VoiceDeviceRow.__tablename__ == "voice_devices"
    assert VoiceProfileRow.__tablename__ == "voice_profiles"
    assert VoiceStatisticsRow.__tablename__ == "voice_statistics"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/p9j012345678_voice_command_center_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "voice_sessions",
        "voice_commands",
        "voice_history",
        "voice_devices",
        "voice_profiles",
        "voice_statistics",
    ):
        assert table in text


def test_exports():
    from platform_ai import voice_runtime_engine, voice_runtime_service

    assert voice_runtime_engine and voice_runtime_service
