"""Voice Command Center service façade — Sprint 36.6."""

from __future__ import annotations

from typing import Any

from platform_ai.voice_engine import VoiceRuntimeEngine, voice_runtime_engine
from platform_ai.voice_models import SpeechProviderId, VoiceIntent, VoiceMode


class VoiceRuntimeService:
    def __init__(self, engine: VoiceRuntimeEngine | None = None) -> None:
        self.engine = engine or voice_runtime_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "voice_runtime",
            "canonical": "platform_ai",
            "sprint": "36.6",
            "modes": [m.value for m in VoiceMode],
            "intents": [i.value for i in VoiceIntent if i != VoiceIntent.UNKNOWN],
            "providers": [p.value for p in SpeechProviderId],
            "fallback_chain": list(self.engine.providers.fallback_chain),
            "statistics": self.engine.statistics(),
            "integrations": [
                "ai_runtime",
                "workflow",
                "service_builder",
                "context_engine",
                "event_bus",
            ],
            "security": {
                "rbac": True,
                "confirmation": True,
                "dangerous_approval": True,
                "audit_logging": True,
                "encrypted_sessions": True,
            },
            "features": {
                "microphone": True,
                "streaming": True,
                "push_to_talk": True,
                "wake_word": True,
                "continuous": True,
                "vad": True,
            },
        }

    async def providers(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        return await self.engine.providers.health_all()

    def start_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.start_session(body).to_dict()

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_sessions()]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def stop_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.stop_session(session_id).to_dict()

    def set_mode(self, session_id: str, mode: str) -> dict[str, Any]:
        return self.engine.set_mode(session_id, mode).to_dict()

    def vad(self, session_id: str, energy: float = 0.5) -> dict[str, Any]:
        return self.engine.vad(session_id, energy=energy)

    def wake_word(self, session_id: str, text: str) -> dict[str, Any]:
        return self.engine.detect_wake_word(session_id, text)

    async def process(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self.engine.process(body)

    async def confirm(self, command_id: str, *, approved_by: str = "system") -> dict[str, Any]:
        return await self.engine.confirm(command_id, approved_by=approved_by)

    def list_commands(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.engine.list_commands(limit=limit)]

    def history(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.engine.timeline(limit=limit)

    def list_devices(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self.engine.list_devices()]

    def register_device(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.register_device(body).to_dict()

    def list_profiles(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.engine.list_profiles()]

    def upsert_profile(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.upsert_profile(body).to_dict()

    def statistics(self) -> dict[str, Any]:
        return self.engine.statistics()

    def parse(self, transcript: str) -> dict[str, Any]:
        return self.engine.parser.parse(transcript).to_dict()

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        result = await self.process(
            {
                "transcript": body.get("transcript") or body.get("text") or "call ai agent to summarize",
                "principal": body.get("principal") or "ai_runtime",
                "confirmed": True,
                "auto_confirm": True,
            }
        )
        return {"consumer": "ai_runtime", **result}

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        result = await self.process(
            {
                "transcript": body.get("transcript") or "launch workflow approval",
                "principal": body.get("principal") or "workflow",
                "confirmed": True,
            }
        )
        return {"consumer": "workflow", **result}

    async def for_service_builder(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "consumer": "service_builder",
            "status": self.status(),
            "devices": self.list_devices(),
            "query": (body or {}).get("query"),
        }

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        parsed = self.parse(str(body.get("transcript") or body.get("query") or "open crm"))
        return {"consumer": "context_engine", "parsed": parsed}


voice_runtime_service = VoiceRuntimeService()
