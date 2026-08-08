"""Per-owner / session mode state."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from platform_modes.mode_state import WorkMode, indicator_ru, parse_mode
from platform_modes.permissions import ModeSettings


@dataclass
class SessionMode:
    owner_id: str
    mode: WorkMode = WorkMode.HUMAN_MODE
    settings: ModeSettings = field(default_factory=ModeSettings)
    updated_at: float = field(default_factory=time.time)
    channel: str = "web"

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "mode": self.mode.value,
            "indicator": indicator_ru(self.mode),
            "settings": self.settings.to_dict(),
            "updated_at": self.updated_at,
            "channel": self.channel,
        }


class SessionModeStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, SessionMode] = {}
        self._defaults: dict[str, WorkMode] = {}
        self._last: dict[str, WorkMode] = {}

    def get(self, owner_id: str) -> SessionMode:
        with self._lock:
            if owner_id not in self._sessions:
                default = self._defaults.get(owner_id) or self._last.get(owner_id, WorkMode.HUMAN_MODE)
                self._sessions[owner_id] = SessionMode(owner_id=owner_id, mode=default)
            return self._sessions[owner_id]

    def set_mode(self, owner_id: str, mode: WorkMode, *, channel: str = "web") -> SessionMode:
        if mode == WorkMode.AUTO_MODE:
            mode = WorkMode.HUMAN_MODE  # not enabled yet
        with self._lock:
            session = self.get(owner_id)
            session.mode = mode
            session.channel = channel
            session.updated_at = time.time()
            self._last[owner_id] = mode
            return session

    def set_default(self, owner_id: str, mode: WorkMode) -> SessionMode:
        if mode == WorkMode.AUTO_MODE:
            mode = WorkMode.HUMAN_MODE
        with self._lock:
            self._defaults[owner_id] = mode
            self._last[owner_id] = mode
            session = self.get(owner_id)
            session.settings.default_mode = mode
            return session

    def update_settings(self, owner_id: str, data: dict[str, Any]) -> SessionMode:
        with self._lock:
            session = self.get(owner_id)
            merged = {**session.settings.to_dict(), **data}
            session.settings = ModeSettings.from_dict(merged)
            if "default_mode" in data:
                dm = session.settings.default_mode
                self._defaults[owner_id] = dm
            return session

    def restore(self, owner_id: str) -> SessionMode:
        with self._lock:
            session = self.get(owner_id)
            if session.settings.remember_last_mode and owner_id in self._last:
                session.mode = self._last[owner_id]
            elif owner_id in self._defaults:
                session.mode = self._defaults[owner_id]
            elif session.settings.start_in_ai:
                session.mode = WorkMode.AI_MODE
            elif session.settings.start_voice_after_login:
                session.mode = WorkMode.VOICE_MODE
            elif session.settings.start_in_human:
                session.mode = WorkMode.HUMAN_MODE
            else:
                session.mode = session.settings.default_mode
            session.updated_at = time.time()
            return session


session_mode_store = SessionModeStore()
