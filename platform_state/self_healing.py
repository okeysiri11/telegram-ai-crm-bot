"""Self-healing runtime — automatic recovery (Sprint 34.2D)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from platform_state.event_store import event_store
from platform_state.models import utcnow
from platform_state.replay import replay_engine
from platform_state.sync_engine import sync_engine
from platform_state.telemetry import enterprise_telemetry

logger = logging.getLogger(__name__)


@dataclass
class HealAction:
    kind: str
    client_id: str | None
    at: str
    detail: dict[str, Any] = field(default_factory=dict)
    ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "client_id": self.client_id,
            "at": self.at,
            "detail": self.detail,
            "ok": self.ok,
        }


class SelfHealingRuntime:
    def __init__(self) -> None:
        self._history: list[HealAction] = []
        self._client_cursors: dict[str, str] = {}

    def note_client_revision(self, client_id: str, revision: str) -> None:
        self._client_cursors[client_id] = revision

    def on_disconnect(self, client_id: str, *, reason: str = "network") -> HealAction:
        action = HealAction(
            kind="disconnect",
            client_id=client_id,
            at=utcnow().isoformat(),
            detail={"reason": reason, "last_revision": self._client_cursors.get(client_id)},
        )
        self._history.append(action)
        enterprise_telemetry.incr("heals")
        return action

    def on_reconnect(
        self,
        client_id: str,
        *,
        last_revision: str | None = None,
        slices: list[str] | None = None,
        client_kind: str = "generic",
    ) -> dict[str, Any]:
        """Telegram / Desktop / Mobile reconnect — deliver delta only."""
        rev = last_revision or self._client_cursors.get(client_id)
        cursor = sync_engine.register_cursor(client_id, last_revision=rev, slices=slices)
        events = sync_engine.delta_since(rev, slices=slices)
        # Durable catch-up if hot window missed events
        durable = []
        if not events and event_store.count() > 0:
            durable = [e.to_dict() for e in event_store.since_seq(max(0, event_store.max_seq() - 200))]
        action = HealAction(
            kind="reconnect",
            client_id=client_id,
            at=utcnow().isoformat(),
            detail={
                "client_kind": client_kind,
                "delta_count": len(events),
                "durable_count": len(durable),
                "revision": cursor.last_revision,
            },
        )
        self._history.append(action)
        enterprise_telemetry.incr("heals")
        if rev:
            self._client_cursors[client_id] = sync_engine.revision
        return {
            "healed": True,
            "action": action.to_dict(),
            "cursor": {
                "client_id": cursor.client_id,
                "last_revision": sync_engine.revision,
            },
            "events": events or durable,
        }

    def on_worker_restart(self) -> dict[str, Any]:
        """Rebuild version heads from durable event store after worker restart."""
        result = replay_engine.replay_all()
        action = HealAction(
            kind="worker_restart",
            client_id=None,
            at=utcnow().isoformat(),
            detail=result.to_dict(),
            ok=len(result.errors) == 0,
        )
        self._history.append(action)
        enterprise_telemetry.incr("heals")
        enterprise_telemetry.incr("replays")
        return {"healed": True, "replay": result.to_dict(), "action": action.to_dict()}

    def on_replay_failure(self, *, error: str, after_seq: int = 0) -> dict[str, Any]:
        """Retry partial replay after failure."""
        try:
            result = replay_engine.replay_all(after_seq=after_seq)
            ok = len(result.errors) == 0
            action = HealAction(
                kind="replay_retry",
                client_id=None,
                at=utcnow().isoformat(),
                detail={"error": error, **result.to_dict()},
                ok=ok,
            )
        except Exception as exc:  # noqa: BLE001
            action = HealAction(
                kind="replay_retry",
                client_id=None,
                at=utcnow().isoformat(),
                detail={"error": error, "retry_error": str(exc)},
                ok=False,
            )
            result = None
        self._history.append(action)
        enterprise_telemetry.incr("heals")
        enterprise_telemetry.incr("failed_syncs" if not action.ok else "replays")
        return {"healed": action.ok, "action": action.to_dict(), "replay": result.to_dict() if result else None}

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._history[-limit:]]

    def reset(self) -> None:
        self._history.clear()
        self._client_cursors.clear()


self_healing = SelfHealingRuntime()
