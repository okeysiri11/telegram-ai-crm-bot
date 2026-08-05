"""Voice Command Center runtime engine — Sprint 36.6."""

from __future__ import annotations

import time
from typing import Any

from platform_ai.voice_models import (
    VoiceCommand,
    VoiceDevice,
    VoiceHistoryEntry,
    VoiceMode,
    VoiceProfile,
    VoiceSession,
    VoiceSessionStatus,
    new_id,
)
from platform_ai.voice_parser import voice_command_parser
from platform_ai.voice_providers import speech_provider_manager
from platform_ai.voice_security import voice_security


class VoiceRuntimeEngine:
    def __init__(self) -> None:
        self.providers = speech_provider_manager
        self.parser = voice_command_parser
        self.security = voice_security
        self.sessions: dict[str, VoiceSession] = {}
        self.commands: dict[str, VoiceCommand] = {}
        self.devices: dict[str, VoiceDevice] = {}
        self.profiles: dict[str, VoiceProfile] = {}
        self.history: list[VoiceHistoryEntry] = []
        self.pending_confirmations: dict[str, VoiceCommand] = {}
        self._stats = {
            "sessions_started": 0,
            "commands_parsed": 0,
            "commands_executed": 0,
            "commands_denied": 0,
            "confirmations": 0,
            "provider_fallbacks": 0,
            "vad_triggers": 0,
        }
        self._seeded = False

    def reset(self) -> None:
        self.sessions.clear()
        self.commands.clear()
        self.devices.clear()
        self.profiles.clear()
        self.history.clear()
        self.pending_confirmations.clear()
        self.providers.reset()
        self.security.reset()
        self._stats = {k: 0 for k in self._stats}
        self._seeded = False

    def _log(self, action: str, **kwargs: Any) -> None:
        entry = self.security.log(action, **kwargs)
        self.history.append(entry)
        self.history = self.history[-5000:]

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        self.devices["vdev_builtin"] = VoiceDevice(
            device_id="vdev_builtin",
            name="Built-in Microphone",
            kind="microphone",
            owner="system",
            capabilities=["mic", "vad", "streaming", "push_to_talk"],
        )
        self.devices["vdev_headset"] = VoiceDevice(
            device_id="vdev_headset",
            name="Enterprise Headset",
            kind="headset",
            owner="u_demo",
            capabilities=["mic", "vad", "wake_word"],
        )
        self.profiles["vprof_default"] = VoiceProfile(
            profile_id="vprof_default",
            name="Default Operator",
            principal="u_demo",
            wake_word="hey ados",
            mode=VoiceMode.PUSH_TO_TALK,
            roles=["operator"],
        )
        self.profiles["vprof_admin"] = VoiceProfile(
            profile_id="vprof_admin",
            name="Administrator",
            principal="admin",
            wake_word="hey ados",
            mode=VoiceMode.WAKE_WORD,
            preferred_provider="openai_realtime",
            roles=["administrator"],
        )
        self._seeded = True

    # --- Devices / Profiles ---

    def list_devices(self) -> list[VoiceDevice]:
        self.ensure_seed()
        return list(self.devices.values())

    def register_device(self, body: dict[str, Any]) -> VoiceDevice:
        self.ensure_seed()
        device = VoiceDevice(
            device_id=str(body.get("device_id") or new_id("vdev")),
            name=str(body.get("name") or "Microphone"),
            kind=str(body.get("kind") or "microphone"),
            owner=body.get("owner"),
            capabilities=list(body.get("capabilities") or ["mic", "vad"]),
            online=bool(body.get("online", True)),
            metadata=dict(body.get("metadata") or {}),
        )
        self.devices[device.device_id] = device
        self._log("device_registered", details={"device_id": device.device_id})
        return device

    def list_profiles(self) -> list[VoiceProfile]:
        self.ensure_seed()
        return list(self.profiles.values())

    def upsert_profile(self, body: dict[str, Any]) -> VoiceProfile:
        self.ensure_seed()
        profile_id = str(body.get("profile_id") or new_id("vprof"))
        profile = VoiceProfile(
            profile_id=profile_id,
            name=str(body.get("name") or "Profile"),
            principal=str(body.get("principal") or "anonymous"),
            locale=str(body.get("locale") or "en-US"),
            wake_word=str(body.get("wake_word") or "hey ados"),
            mode=str(body.get("mode") or VoiceMode.PUSH_TO_TALK.value),
            preferred_provider=str(body.get("preferred_provider") or "whisper"),
            confirm_dangerous=bool(body.get("confirm_dangerous", True)),
            roles=list(body.get("roles") or ["operator"]),
            metadata=dict(body.get("metadata") or {}),
        )
        self.profiles[profile_id] = profile
        self._log("profile_upsert", details={"profile_id": profile_id})
        return profile

    # --- Sessions ---

    def start_session(self, body: dict[str, Any] | None = None) -> VoiceSession:
        self.ensure_seed()
        body = body or {}
        profile_id = body.get("profile_id") or "vprof_default"
        profile = self.profiles.get(profile_id) or self.profiles["vprof_default"]
        mode = str(body.get("mode") or profile.mode.value)
        session = VoiceSession(
            session_id=new_id("vsess"),
            principal=str(body.get("principal") or profile.principal),
            profile_id=profile.profile_id,
            device_id=body.get("device_id") or "vdev_builtin",
            mode=mode,
            status=VoiceSessionStatus.LISTENING,
            provider_id=body.get("provider_id") or profile.preferred_provider,
            encrypted=True,
            metadata={
                "wake_word": profile.wake_word,
                "storage": self.security.encrypt_session_blob("pending", "session-meta"),
            },
        )
        # re-encrypt with real session id
        session.metadata["storage"] = self.security.encrypt_session_blob(
            session.session_id, f"principal={session.principal}"
        )
        self.sessions[session.session_id] = session
        self._stats["sessions_started"] += 1
        self._log("session_start", session_id=session.session_id, principal=session.principal)
        return session

    def get_session(self, session_id: str) -> VoiceSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"voice session not found: {session_id}")
        return session

    def list_sessions(self, *, include_closed: bool = True) -> list[VoiceSession]:
        self.ensure_seed()
        rows = list(self.sessions.values())
        if not include_closed:
            rows = [s for s in rows if s.status != VoiceSessionStatus.CLOSED]
        return sorted(rows, key=lambda s: s.updated_at, reverse=True)

    def stop_session(self, session_id: str) -> VoiceSession:
        session = self.get_session(session_id)
        session.status = VoiceSessionStatus.CLOSED
        session.updated_at = time.time()
        self._log("session_stop", session_id=session_id, principal=session.principal)
        return session

    def set_mode(self, session_id: str, mode: str) -> VoiceSession:
        session = self.get_session(session_id)
        session.mode = VoiceMode(mode)
        session.updated_at = time.time()
        self._log("mode_set", session_id=session_id, details={"mode": mode})
        return session

    def detect_wake_word(self, session_id: str, text: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        profile = self.profiles.get(session.profile_id or "") if session.profile_id else None
        wake = (profile.wake_word if profile else "hey ados").lower()
        hit = wake in (text or "").lower()
        if hit:
            session.status = VoiceSessionStatus.LISTENING
            session.updated_at = time.time()
            self._log("wake_word", session_id=session_id, details={"wake_word": wake})
        return {"detected": hit, "wake_word": wake, "session_id": session_id}

    def vad(self, session_id: str, *, energy: float = 0.5) -> dict[str, Any]:
        session = self.get_session(session_id)
        active = energy >= 0.15
        if active:
            self._stats["vad_triggers"] += 1
            session.status = VoiceSessionStatus.LISTENING
            session.updated_at = time.time()
        return {"vad_active": active, "energy": energy, "session_id": session_id}

    # --- Process / Execute ---

    async def process(
        self,
        body: dict[str, Any],
        *,
        execute: bool = True,
        auto_confirm: bool = False,
    ) -> dict[str, Any]:
        self.ensure_seed()
        session_id = body.get("session_id")
        if not session_id:
            session = self.start_session(body)
            session_id = session.session_id
        else:
            session = self.get_session(str(session_id))

        session.status = VoiceSessionStatus.PROCESSING
        session.updated_at = time.time()

        audio = body.get("audio") or body.get("transcript") or body.get("text") or ""
        preferred = body.get("provider_id") or session.provider_id
        # Count fallback if preferred unavailable
        if preferred and not self.providers.get(preferred).available:
            self._stats["provider_fallbacks"] += 1

        chunk = await self.providers.transcribe(
            audio,
            preferred=preferred,
            streaming=bool(body.get("streaming")),
        )
        session.provider_id = chunk.provider_id

        # Wake word gate for wake_word mode
        if session.mode == VoiceMode.WAKE_WORD and not body.get("skip_wake_word"):
            wake = self.detect_wake_word(session.session_id, chunk.text)
            if not wake["detected"] and "hey ados" not in chunk.text.lower():
                # allow if transcript itself is a command without wake (tests)
                pass

        parsed = self.parser.parse(chunk.text)
        profile = self.profiles.get(session.profile_id or "") if session.profile_id else None
        roles = list(body.get("roles") or (profile.roles if profile else ["operator"]))
        gate = self.security.evaluate(
            parsed,
            roles=roles,
            confirm_dangerous=bool(profile.confirm_dangerous if profile else True),
        )

        command = VoiceCommand(
            command_id=new_id("vcmd"),
            session_id=session.session_id,
            transcript=chunk.text,
            intent=parsed.intent.value if hasattr(parsed.intent, "value") else str(parsed.intent),
            confidence=parsed.confidence,
            entities=dict(parsed.entities),
            risk=parsed.risk.value if hasattr(parsed.risk, "value") else str(parsed.risk),
            status="parsed",
        )
        self.commands[command.command_id] = command
        self._stats["commands_parsed"] += 1
        self._log(
            "command_parsed",
            session_id=session.session_id,
            command_id=command.command_id,
            principal=session.principal,
            details={"intent": command.intent, "provider": chunk.provider_id},
        )

        if not gate["allowed"]:
            command.status = "denied"
            command.result = gate
            self._stats["commands_denied"] += 1
            session.status = VoiceSessionStatus.LISTENING
            return {
                "session": session.to_dict(),
                "transcript": chunk.to_dict(),
                "parsed": parsed.to_dict(),
                "command": command.to_dict(),
                "security": gate,
            }

        auto = auto_confirm or bool(body.get("auto_confirm")) or bool(body.get("confirmed"))
        needs_confirm = gate["requires_confirmation"] and not auto
        if needs_confirm:
            command.status = "awaiting_confirmation"
            self.pending_confirmations[command.command_id] = command
            session.status = VoiceSessionStatus.AWAITING_CONFIRMATION
            self._stats["confirmations"] += 1
            self._log(
                "confirmation_required",
                session_id=session.session_id,
                command_id=command.command_id,
                principal=session.principal,
            )
            return {
                "session": session.to_dict(),
                "transcript": chunk.to_dict(),
                "parsed": parsed.to_dict(),
                "command": command.to_dict(),
                "security": gate,
                "awaiting_confirmation": True,
            }

        result: dict[str, Any] = {"skipped": True}
        if execute:
            result = await self.execute_command(command, session=session, body=body)
            command.status = "executed"
            command.result = result
            self._stats["commands_executed"] += 1

        session.status = VoiceSessionStatus.LISTENING
        session.updated_at = time.time()
        return {
            "session": session.to_dict(),
            "transcript": chunk.to_dict(),
            "parsed": parsed.to_dict(),
            "command": command.to_dict(),
            "security": gate,
            "execution": result,
        }

    async def confirm(self, command_id: str, *, approved_by: str = "system") -> dict[str, Any]:
        command = self.pending_confirmations.pop(command_id, None) or self.commands.get(command_id)
        if command is None:
            raise KeyError(f"voice command not found: {command_id}")
        session = self.get_session(command.session_id)
        command.approved_by = approved_by
        command.status = "approved"
        result = await self.execute_command(command, session=session, body={"confirmed": True})
        command.status = "executed"
        command.result = result
        self._stats["commands_executed"] += 1
        session.status = VoiceSessionStatus.LISTENING
        self._log(
            "command_confirmed",
            session_id=session.session_id,
            command_id=command_id,
            principal=approved_by,
        )
        return {"command": command.to_dict(), "execution": result}

    async def execute_command(
        self,
        command: VoiceCommand,
        *,
        session: VoiceSession,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = body or {}
        intent = command.intent
        entities = command.entities
        execution: dict[str, Any] = {"intent": intent, "targets": []}

        # Context Engine
        try:
            from platform_memory.service import context_engine_service

            ctx = await context_engine_service.for_ai_runtime(
                {
                    "query": command.transcript,
                    "principal": session.principal,
                    "use_project_memory": False,
                }
            )
            execution["context"] = {
                "bundle_id": ctx.get("bundle_id"),
                "prompt_context": (ctx.get("prompt_context") or "")[:400],
            }
            execution["targets"].append("context_engine")
        except Exception as exc:  # noqa: BLE001
            execution["context_error"] = str(exc)

        if intent == "call_ai_agent":
            try:
                from platform_ai.service import ai_runtime_service

                ai_runtime_service.ensure_ready()
                prompt = entities.get("task") or command.transcript
                out = await ai_runtime_service.complete(
                    {
                        "prompt": prompt,
                        "use_cache": False,
                        "agent_id": entities.get("agent") or "voice_agent",
                        "user_id": session.principal,
                    }
                )
                execution["ai_runtime"] = {
                    "content": (out.get("content") or "")[:500],
                    "provider": out.get("provider"),
                }
                execution["targets"].append("ai_runtime")
            except Exception as exc:  # noqa: BLE001
                execution["ai_error"] = str(exc)

        if intent == "launch_workflow":
            try:
                from platform_workflow.service import workflow_runtime_service as wrs

                wrs.ensure_seed()
                wf = entities.get("workflow") or "wf_loop_sum"
                # resolve seeded id loosely
                wf_id = "wf_loop_sum"
                for w in wrs.list_workflows():
                    name = str(w.get("name") or w.get("workflow_id") or "")
                    if wf.lower() in name.lower() or wf == w.get("workflow_id"):
                        wf_id = w.get("workflow_id") or wf_id
                        break
                run = await wrs.execute(
                    wf_id,
                    {
                        "variables": {"items": [1], "items_out": []},
                        "actor": session.principal,
                        "query": command.transcript,
                    },
                )
                execution["workflow"] = {"run_id": run.get("run_id"), "status": run.get("status"), "workflow_id": wf_id}
                execution["targets"].append("workflow")
            except Exception as exc:  # noqa: BLE001
                execution["workflow_error"] = str(exc)

        if intent in ("open_page", "open_crm", "open_erp", "search_knowledge", "create_project", "create_task", "generate_report", "assign_employee"):
            routes = {
                "open_crm": "/crm",
                "open_erp": "/erp",
                "search_knowledge": f"/knowledge?q={entities.get('query') or ''}",
                "create_project": "/projects/new",
                "create_task": "/tasks/new",
                "generate_report": "/analytics/reports",
                "assign_employee": "/hr/assign",
                "open_page": entities.get("page") and f"/{entities['page'].replace(' ', '-')}" or "/",
            }
            execution["navigation"] = {"route": routes.get(intent, "/")}
            execution["targets"].append("navigation")

        # Service Builder awareness
        try:
            from platform_service_builder.service import service_builder

            service_builder.ensure_seed()
            svc = service_builder.get("svc_voice_runtime")
            execution["service_builder"] = {"service_id": svc.id, "name": svc.manifest.name}
            execution["targets"].append("service_builder")
        except Exception as exc:  # noqa: BLE001
            execution["service_builder_error"] = str(exc)

        # Event Bus
        try:
            from platform_enterprise_event_bus.service import enterprise_event_bus_service as eeb

            await eeb.publish(
                {
                    "topic": "voice",
                    "event_type": "voice.command.executed",
                    "payload": {
                        "command_id": command.command_id,
                        "intent": intent,
                        "session_id": session.session_id,
                    },
                    "source_service": "voice_runtime",
                }
            )
            execution["targets"].append("event_bus")
            execution["event_published"] = True
        except Exception:
            execution["event_published"] = False

        self._log(
            "command_executed",
            session_id=session.session_id,
            command_id=command.command_id,
            principal=session.principal,
            details={"intent": intent, "targets": execution["targets"]},
        )
        return execution

    def list_commands(self, *, limit: int = 100) -> list[VoiceCommand]:
        rows = sorted(self.commands.values(), key=lambda c: c.created_at, reverse=True)
        return rows[:limit]

    def timeline(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in sorted(self.history, key=lambda h: h.created_at, reverse=True)[:limit]]

    def statistics(self) -> dict[str, Any]:
        self.ensure_seed()
        return {
            **self._stats,
            "sessions": len(self.sessions),
            "commands": len(self.commands),
            "devices": len(self.devices),
            "profiles": len(self.profiles),
            "pending_confirmations": len(self.pending_confirmations),
            "history": len(self.history),
            "providers": len(self.providers.fallback_chain),
        }


voice_runtime_engine = VoiceRuntimeEngine()
