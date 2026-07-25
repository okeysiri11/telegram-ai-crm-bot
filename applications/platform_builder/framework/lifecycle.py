"""Universal Builder lifecycle pipeline — Sprint 28.5."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.framework.catalogs import LIFECYCLE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LifecycleEngine:
    """Common lifecycle: Initialize → Configure → Validate → Preview → Summary → Create → Register → Finish."""

    def __init__(self) -> None:
        self.phases = list(LIFECYCLE)

    def start(self, builder_type: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "builder_type": builder_type,
            "phase": "initialize",
            "phase_index": 0,
            "phases": list(self.phases),
            "config": config or {},
            "history": [{"phase": "initialize", "at": _now()}],
            "status": "running",
        }

    def advance(self, state: dict[str, Any], *, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        idx = int(state.get("phase_index") or 0)
        if idx >= len(self.phases) - 1:
            state["status"] = "finished"
            state["phase"] = "finish"
            return state
        idx += 1
        state["phase_index"] = idx
        state["phase"] = self.phases[idx]
        if patch:
            state["config"] = {**(state.get("config") or {}), **patch}
        history = list(state.get("history") or [])
        history.append({"phase": state["phase"], "at": _now()})
        state["history"] = history
        if state["phase"] == "finish":
            state["status"] = "finished"
        return state

    def run_to(self, state: dict[str, Any], phase: str) -> dict[str, Any]:
        if phase not in self.phases:
            raise ValueError(f"Unknown lifecycle phase: {phase}")
        target = self.phases.index(phase)
        while int(state.get("phase_index") or 0) < target:
            state = self.advance(state)
        return state

    def status(self) -> dict[str, Any]:
        return {"ready": True, "phases": list(self.phases), "count": len(self.phases)}
