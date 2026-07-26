"""Enterprise Command Center OS & Universal Command Platform — Sprint 29.13.

Universal control layer for the Enterprise AI Platform.
Orchestrates user interaction only — never implements business logic.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.command_center.catalogs import (
    ASSISTANT_FEATURES,
    COMMAND_CATEGORIES,
    COMMAND_CENTER_COMPONENTS,
    DEFAULT_COMMANDS,
    DEFAULT_SHORTCUTS,
    EXECUTION_TYPES,
    HISTORY_FEATURES,
    HOTKEY_FEATURES,
    PALETTE_FEATURES,
    PERFORMANCE_FEATURES,
    UI_SURFACES,
    VOICE_APIS,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class CommandDispatcher:
    """Dispatches registered commands as interaction intents — no business logic."""

    def __init__(self) -> None:
        self.commands = [dict(c) for c in DEFAULT_COMMANDS]
        self.history: list[dict[str, Any]] = []
        self.favorites: set[str] = set()
        self.pinned: set[str] = set()
        self.usage: Counter[str] = Counter()
        self.shortcuts = {k: dict(v) for k, v in DEFAULT_SHORTCUTS.items()}
        self.shortcut_profile = "default"
        self.cache = {"enabled": True, "entries": 0, "index_size": len(DEFAULT_COMMANDS)}
        self.voice = {
            "voice_commands": True,
            "speech_recognition_interface": True,
            "speech_feedback": True,
            "future_voice_assistant": "prepared",
            "listening": False,
            "last_transcript": None,
        }
        self.context = {"workspace": None, "module": None, "role": "manager"}

    def status(self) -> dict[str, Any]:
        return {
            "command_count": len(self.commands),
            "history_count": len(self.history),
            "favorites": len(self.favorites),
            "pinned": len(self.pinned),
            "shortcut_profile": self.shortcut_profile,
            "cache_enabled": self.cache["enabled"],
            "voice_ready": True,
            "executes_business_logic": False,
            "ready": True,
        }


class EnterpriseCommandCenter:
    """Enterprise Command Center OS — universal command interaction layer."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.dispatcher = CommandDispatcher()

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.13",
            "command_center_ready": True,
            "universal_command_platform_ready": True,
            "voice_foundation_ready": True,
            "ai_command_assistant_ready": True,
            "shortcut_engine_ready": True,
            "executes_business_logic": False,
            "orchestrates_user_interaction_only": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.13",
            "executes_business_logic": False,
            "orchestrates_user_interaction_only": True,
            "components": list(COMMAND_CENTER_COMPONENTS),
            "registered": len(self.store.command_centers.list_all()),
            "dispatcher": self.dispatcher.status(),
        }

    # Step 1
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Enterprise Command Center OS",
            "components": list(COMMAND_CENTER_COMPONENTS),
            "dispatcher": self.dispatcher.status(),
            "executes_business_logic": False,
            "orchestrates_user_interaction_only": True,
            "ready": True,
        }

    # Step 2 — Global Command Palette
    def command_palette(self, query: str | None = None) -> dict[str, Any]:
        results = self._search(query) if query else list(self.dispatcher.commands)
        recent = [h["command_id"] for h in self.dispatcher.history[-5:]]
        return {
            "features": list(PALETTE_FEATURES),
            "supported": {f: True for f in PALETTE_FEATURES},
            "query": query,
            "results": results,
            "recent": recent,
            "favorites": sorted(self.dispatcher.favorites),
            "ready": True,
        }

    # Step 3 — Command Execution
    def execute_command(self, command_id: str | None = None) -> dict[str, Any]:
        if command_id:
            cmd = next((c for c in self.dispatcher.commands if c["id"] == command_id), None)
            if not cmd:
                raise NotFoundError(f"Command not found: {command_id}")
            record = {
                "execution_id": _id("cx"),
                "command_id": command_id,
                "title": cmd["title"],
                "execution_type": cmd["execution_type"],
                "at": _now(),
                "intent_only": True,
                "executes_business_logic": False,
            }
            self.dispatcher.history.append(record)
            self.dispatcher.usage[command_id] += 1
            self.dispatcher.cache["entries"] = self.dispatcher.cache.get("entries", 0) + 1
            return {
                "ok": True,
                "execution": record,
                "execution_types": list(EXECUTION_TYPES),
                "message": f"Dispatched interaction intent for «{cmd['title']}».",
                "ready": True,
            }
        return {
            "execution_types": list(EXECUTION_TYPES),
            "supported": {t: True for t in EXECUTION_TYPES},
            "recent": list(self.dispatcher.history[-10:]),
            "ready": True,
        }

    # Step 4 — Categories
    def categories(self) -> dict[str, Any]:
        by_cat: dict[str, list[str]] = {c: [] for c in COMMAND_CATEGORIES}
        for cmd in self.dispatcher.commands:
            by_cat.setdefault(cmd["category"], []).append(cmd["id"])
        return {
            "categories": list(COMMAND_CATEGORIES),
            "commands_by_category": by_cat,
            "ready": True,
        }

    # Step 5 — Voice Foundation
    def voice_foundation(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            if "listening" in patch:
                self.dispatcher.voice["listening"] = bool(patch["listening"])
            if "transcript" in patch:
                self.dispatcher.voice["last_transcript"] = patch["transcript"]
                self.dispatcher.voice["last_feedback"] = f"Heard: {patch['transcript']}"
        return {
            "apis": list(VOICE_APIS),
            "prepared": {a: True for a in VOICE_APIS},
            "state": dict(self.dispatcher.voice),
            "voice_foundation_ready": True,
            "ready": True,
        }

    # Step 6 — Hotkey Engine
    def hotkey_engine(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            if "profile" in patch:
                self.dispatcher.shortcut_profile = str(patch["profile"])
            if "custom" in patch and isinstance(patch["custom"], dict):
                self.dispatcher.shortcuts.setdefault("Custom Shortcuts", {}).update(patch["custom"])
        return {
            "features": list(HOTKEY_FEATURES),
            "supported": {f: True for f in HOTKEY_FEATURES},
            "shortcuts": {k: dict(v) for k, v in self.dispatcher.shortcuts.items()},
            "profile": self.dispatcher.shortcut_profile,
            "ready": True,
        }

    # Step 7 — Command History
    def command_history(self, *, action: str | None = None, command_id: str | None = None) -> dict[str, Any]:
        if action == "favorite" and command_id:
            self.dispatcher.favorites.add(command_id)
        elif action == "pin" and command_id:
            self.dispatcher.pinned.add(command_id)
        elif action == "unfavorite" and command_id:
            self.dispatcher.favorites.discard(command_id)
        frequent = [cid for cid, _ in self.dispatcher.usage.most_common(5)]
        suggestions = [c["id"] for c in self.dispatcher.commands if c["id"] not in frequent][:3]
        return {
            "features": list(HISTORY_FEATURES),
            "history": list(self.dispatcher.history[-50:]),
            "frequently_used": frequent,
            "pinned": sorted(self.dispatcher.pinned),
            "favorites": sorted(self.dispatcher.favorites),
            "suggestions": suggestions,
            "ready": True,
        }

    # Step 8 — AI Command Assistant
    def ai_assistant(
        self,
        *,
        utterance: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if context:
            self.dispatcher.context.update(context)
        suggestions: list[dict[str, Any]] = []
        autocomplete: list[str] = []
        matched = None
        if utterance:
            matched_cmds = self._search(utterance)
            suggestions = matched_cmds[:5]
            autocomplete = [c["title"] for c in matched_cmds[:5]]
            if matched_cmds:
                matched = matched_cmds[0]
        else:
            suggestions = [
                c
                for c in self.dispatcher.commands
                if c["id"] in self.dispatcher.favorites or self.dispatcher.usage[c["id"]] > 0
            ][:5] or list(self.dispatcher.commands)[:3]
            autocomplete = [c["title"] for c in self.dispatcher.commands[:5]]
        return {
            "features": list(ASSISTANT_FEATURES),
            "supported": {f: True for f in ASSISTANT_FEATURES},
            "utterance": utterance,
            "context": dict(self.dispatcher.context),
            "suggestions": suggestions,
            "autocomplete": autocomplete,
            "matched": matched,
            "smart_recommendations": suggestions[:3],
            "ai_command_assistant_ready": True,
            "executes_business_logic": False,
            "ready": True,
        }

    # Step 9 — Performance
    def performance(self, *, action: str | None = None) -> dict[str, Any]:
        if action == "warm_cache":
            self.dispatcher.cache["entries"] = self.dispatcher.cache.get("entries", 0) + len(
                self.dispatcher.commands
            )
            self.dispatcher.cache["warmed_at"] = _now()
        elif action == "optimize_index":
            self.dispatcher.cache["index_size"] = len(self.dispatcher.commands)
            self.dispatcher.cache["optimized_at"] = _now()
        return {
            "features": list(PERFORMANCE_FEATURES),
            "enabled": {f: True for f in PERFORMANCE_FEATURES},
            "cache": dict(self.dispatcher.cache),
            "fast_search": True,
            "realtime_suggestions": True,
            "ready": True,
        }

    # UI
    def ui_dashboard(self) -> dict[str, Any]:
        return {
            "surfaces": list(UI_SURFACES),
            "command_palette": self.command_palette(),
            "quick_launcher": {
                "favorites": sorted(self.dispatcher.favorites),
                "frequent": [cid for cid, _ in self.dispatcher.usage.most_common(5)],
            },
            "command_history": self.command_history(),
            "shortcut_manager": self.hotkey_engine(),
            "voice_console": self.voice_foundation(),
            "ai_suggestions": self.ai_assistant(),
            "executes_business_logic": False,
            "ready": True,
        }

    def _search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower().strip()
        results: list[dict[str, Any]] = []
        for cmd in self.dispatcher.commands:
            hay = " ".join([cmd["title"], cmd["category"], cmd["execution_type"], *cmd["keywords"]]).lower()
            if q in hay:
                results.append(dict(cmd))
        return results

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("ccwz")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.command_center_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.command_center_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Command Center session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session.get("draft", {}), **patch["draft"]}
        session["updated_at"] = _now()
        self.store.command_center_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Enterprise Command Center Summary",
            "core": self.engine_overview(),
            "palette": self.command_palette(),
            "execution": self.execute_command(),
            "categories": self.categories(),
            "voice": self.voice_foundation(),
            "hotkeys": self.hotkey_engine(),
            "history": self.command_history(),
            "assistant": self.ai_assistant(),
            "performance": self.performance(),
            "ui": self.ui_dashboard(),
            "steps": WIZARD_STEPS,
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)

        cc_id = _id("cceng")
        reg_id = _id("ccreg")
        api_id = _id("ccapi")
        short_id = _id("ccsh")
        voice_id = _id("ccvo")

        command_center = {
            "command_center_id": cc_id,
            "internal_id": cc_id,
            "catalog": self.catalog(),
            "executes_business_logic": False,
            "orchestrates_user_interaction_only": True,
            "registered_at": _now(),
            "sprint": "29.13",
        }
        command_registry = {
            "command_registry_id": reg_id,
            "internal_id": reg_id,
            "commands": [dict(c) for c in self.dispatcher.commands],
            "categories": list(COMMAND_CATEGORIES),
            "registered_at": _now(),
            "sprint": "29.13",
        }
        command_api = {
            "command_api_id": api_id,
            "internal_id": api_id,
            "endpoints": [
                "palette",
                "execute",
                "categories",
                "voice",
                "hotkeys",
                "history",
                "assistant",
                "performance",
            ],
            "registered_at": _now(),
            "sprint": "29.13",
        }
        shortcut_engine = {
            "shortcut_engine_id": short_id,
            "internal_id": short_id,
            "features": list(HOTKEY_FEATURES),
            "shortcuts": {k: dict(v) for k, v in self.dispatcher.shortcuts.items()},
            "registered_at": _now(),
            "sprint": "29.13",
        }
        voice_api = {
            "voice_api_id": voice_id,
            "internal_id": voice_id,
            "apis": list(VOICE_APIS),
            "voice_foundation_ready": True,
            "registered_at": _now(),
            "sprint": "29.13",
        }

        self.store.command_centers.save(cc_id, command_center)
        self.store.command_registries.save(reg_id, command_registry)
        self.store.command_apis.save(api_id, command_api)
        self.store.shortcut_engines.save(short_id, shortcut_engine)
        self.store.voice_apis.save(voice_id, voice_api)

        session["status"] = "created"
        session["registrations"] = {
            "command_center_id": cc_id,
            "command_registry_id": reg_id,
            "command_api_id": api_id,
            "shortcut_engine_id": short_id,
            "voice_api_id": voice_id,
        }
        session["updated_at"] = _now()
        self.store.command_center_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "command_center": command_center,
            "command_registry": command_registry,
            "command_api": command_api,
            "shortcut_engine": shortcut_engine,
            "voice_api": voice_api,
            "message": (
                "Command Center, Command Registry, Command API, "
                "Shortcut Engine, and Voice API registered."
            ),
        }
