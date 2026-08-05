"""Global Version Engine — Sprint 34.2D / TD-54.

Every mutation increments version. No client may bypass this engine for shared state.
Supports optimistic locking, revision history, snapshots, rollback, compare.
"""

from __future__ import annotations

import copy
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from platform_state.entity import CanonicalEntity
from platform_state.event_store import PlatformEventStore, event_store
from platform_state.models import EntityMeta, utcnow


@dataclass
class VersionRecord:
    entity_type: str
    entity_id: str
    version: int
    change_id: str
    snapshot: dict[str, Any]
    updated_at: str
    updated_by: str | None
    source_client: str | None
    workspace_id: str | None = None
    tenant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
            "change_id": self.change_id,
            "snapshot": self.snapshot,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "source_client": self.source_client,
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
        }


class OptimisticLockError(Exception):
    def __init__(self, expected: int, actual: int, entity_type: str, entity_id: str) -> None:
        self.expected = expected
        self.actual = actual
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            f"optimistic lock failed {entity_type}:{entity_id} "
            f"expected={expected} actual={actual}"
        )


class VersionEngine:
    def __init__(self, store: PlatformEventStore | None = None) -> None:
        self._store = store or event_store
        self._heads: dict[str, CanonicalEntity] = {}
        self._history: dict[str, list[VersionRecord]] = {}
        self._lock = threading.RLock()

    @staticmethod
    def key(entity_type: str, entity_id: str) -> str:
        return f"{entity_type}:{entity_id}"

    def get(self, entity_type: str, entity_id: str) -> CanonicalEntity | None:
        with self._lock:
            return copy.deepcopy(self._heads.get(self.key(entity_type, entity_id)))

    def require(self, entity_type: str, entity_id: str) -> CanonicalEntity:
        ent = self.get(entity_type, entity_id)
        if ent is None:
            raise KeyError(f"entity not found: {entity_type}:{entity_id}")
        return ent

    def meta(self, entity_type: str, entity_id: str) -> EntityMeta:
        ent = self.get(entity_type, entity_id)
        if ent is None:
            return EntityMeta(entity_type=entity_type, entity_id=entity_id)
        return EntityMeta(
            entity_type=entity_type,
            entity_id=entity_id,
            version=ent.version,
            updated_at=ent.updated_at,
            updated_by=ent.updated_by,
            source_client=ent.source_client,
        )

    def create(
        self,
        *,
        entity_type: str,
        data: dict[str, Any] | None = None,
        entity_id: str | None = None,
        created_by: str | None = None,
        workspace_id: str | None = None,
        tenant_id: str | None = None,
        source_client: str | None = None,
        metadata: dict[str, Any] | None = None,
        event_type: str | None = None,
        persist_event: bool = True,
    ) -> CanonicalEntity:
        ent = CanonicalEntity.create(
            entity_type=entity_type,
            data=data,
            entity_id=entity_id,
            created_by=created_by,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            source_client=source_client,
            metadata=metadata,
        )
        with self._lock:
            k = self.key(entity_type, ent.id)
            if k in self._heads:
                raise ValueError(f"entity already exists: {k}")
            self._heads[k] = ent
            self._push_history(ent)
        if persist_event:
            self._store.append(
                event_type=event_type or f"{entity_type.title().replace('_', '')}Created",
                entity_type=entity_type,
                entity_id=ent.id,
                payload={"action": "created"},
                before=None,
                after=ent.to_dict(),
                version=ent.version,
                actor_id=created_by,
                source_client=source_client,
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                change_id=ent.change_id,
            )
        return copy.deepcopy(ent)

    def update(
        self,
        *,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any] | None = None,
        expected_version: int | None = None,
        updated_by: str | None = None,
        source_client: str | None = None,
        metadata: dict[str, Any] | None = None,
        event_type: str | None = None,
        soft_delete: bool = False,
        persist_event: bool = True,
        agent_id: str | None = None,
    ) -> CanonicalEntity:
        with self._lock:
            k = self.key(entity_type, entity_id)
            current = self._heads.get(k)
            if current is None:
                # Auto-bootstrap missing head so adapters can version existing SoR ids
                current = CanonicalEntity.create(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    data=data or {},
                    created_by=updated_by,
                    source_client=source_client,
                    metadata=metadata,
                )
                self._heads[k] = current
                self._push_history(current)
                if expected_version is not None and expected_version not in (0, 1):
                    raise OptimisticLockError(expected_version, 1, entity_type, entity_id)
                before = None
            else:
                if expected_version is not None and current.version != expected_version:
                    raise OptimisticLockError(
                        expected_version, current.version, entity_type, entity_id
                    )
                before = current.to_dict()
                current.bump(
                    updated_by=updated_by,
                    source_client=source_client,
                    data=data,
                    metadata=metadata,
                    soft_delete=soft_delete,
                )
                self._push_history(current)
            after = current.to_dict()
            result = copy.deepcopy(current)
        if persist_event:
            self._store.append(
                event_type=event_type or f"{entity_type.title().replace('_', '')}Updated",
                entity_type=entity_type,
                entity_id=entity_id,
                payload={"action": "deleted" if soft_delete else "updated"},
                before=before,
                after=after,
                version=result.version,
                actor_id=updated_by,
                source_client=source_client,
                workspace_id=result.workspace_id,
                tenant_id=result.tenant_id,
                change_id=result.change_id,
                agent_id=agent_id,
            )
        return result

    def _push_history(self, ent: CanonicalEntity) -> None:
        k = self.key(ent.entity_type, ent.id)
        rec = VersionRecord(
            entity_type=ent.entity_type,
            entity_id=ent.id,
            version=ent.version,
            change_id=ent.change_id,
            snapshot=copy.deepcopy(ent.to_dict()),
            updated_at=ent.updated_at,
            updated_by=ent.updated_by,
            source_client=ent.source_client,
            workspace_id=ent.workspace_id,
            tenant_id=ent.tenant_id,
        )
        self._history.setdefault(k, []).append(rec)

    def history(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self._history.get(self.key(entity_type, entity_id), [])]

    def snapshot_at(self, entity_type: str, entity_id: str, version: int) -> dict[str, Any] | None:
        with self._lock:
            for rec in self._history.get(self.key(entity_type, entity_id), []):
                if rec.version == version:
                    return copy.deepcopy(rec.snapshot)
        return None

    def compare(
        self,
        entity_type: str,
        entity_id: str,
        left_version: int,
        right_version: int,
    ) -> dict[str, Any]:
        left = self.snapshot_at(entity_type, entity_id, left_version)
        right = self.snapshot_at(entity_type, entity_id, right_version)
        if left is None or right is None:
            return {
                "left": left,
                "right": right,
                "diff": None,
                "error": "missing_version",
            }
        left_data = left.get("data") or {}
        right_data = right.get("data") or {}
        keys = set(left_data) | set(right_data)
        diff = {
            k: {"old": left_data.get(k), "new": right_data.get(k)}
            for k in sorted(keys)
            if left_data.get(k) != right_data.get(k)
        }
        meta_diff = {
            f: {"old": left.get(f), "new": right.get(f)}
            for f in ("version", "updated_by", "source_client", "change_id", "deleted_at")
            if left.get(f) != right.get(f)
        }
        return {"left": left, "right": right, "diff": diff, "meta_diff": meta_diff}

    def rollback(
        self,
        *,
        entity_type: str,
        entity_id: str,
        to_version: int,
        updated_by: str | None = None,
        source_client: str | None = None,
    ) -> CanonicalEntity:
        snap = self.snapshot_at(entity_type, entity_id, to_version)
        if snap is None:
            raise KeyError(f"no snapshot for version {to_version}")
        restored = CanonicalEntity.from_dict(snap)
        # Roll forward as a new version that restores prior state
        return self.update(
            entity_type=entity_type,
            entity_id=entity_id,
            data=restored.data,
            updated_by=updated_by,
            source_client=source_client,
            metadata={**(restored.metadata or {}), "rolled_back_to": to_version},
            event_type="EntityRolledBack",
        )

    def apply_from_event(self, after: dict[str, Any]) -> CanonicalEntity:
        """Rebuild/overwrite head from an event `after` payload (replay)."""
        ent = CanonicalEntity.from_dict(after)
        with self._lock:
            k = self.key(ent.entity_type, ent.id)
            self._heads[k] = ent
            hist = self._history.setdefault(k, [])
            if not hist or hist[-1].version < ent.version:
                self._push_history(ent)
        return copy.deepcopy(ent)

    def bump_compat(
        self,
        entity_type: str,
        entity_id: str,
        *,
        updated_by: str | None = None,
        source_client: str | None = None,
        data: dict[str, Any] | None = None,
        event_type: str | None = None,
        workspace_id: str | None = None,
        tenant_id: str | None = None,
        agent_id: str | None = None,
        persist_event: bool = False,
    ) -> EntityMeta:
        """Adapter-friendly bump that returns EntityMeta (34.2C compatibility).

        Default persist_event=False — SyncEngine durable-logs the published change.
        """
        ent = self.update(
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            updated_by=updated_by,
            source_client=source_client,
            event_type=event_type,
            agent_id=agent_id,
            persist_event=persist_event,
        )
        if workspace_id or tenant_id:
            with self._lock:
                head = self._heads[self.key(entity_type, entity_id)]
                if workspace_id:
                    head.workspace_id = workspace_id
                if tenant_id:
                    head.tenant_id = tenant_id
        return EntityMeta(
            entity_type=entity_type,
            entity_id=entity_id,
            version=ent.version,
            updated_at=ent.updated_at,
            updated_by=ent.updated_by,
            source_client=ent.source_client,
        )

    def reset(self) -> None:
        with self._lock:
            self._heads.clear()
            self._history.clear()

    def warm_start(self, *, after_seq: int = 0) -> dict[str, Any]:
        """
        HA warm-start: rebuild heads from durable Event Store (Sprint 35.1).
        Safe to call on worker restart — public API unchanged.
        """
        from platform_state.replay import replay_engine

        result = replay_engine.replay_all(after_seq=after_seq)
        self.checkpoint_heads()
        return {"warm_started": True, "replay": result.to_dict(), "heads": len(self._heads)}

    def checkpoint_heads(self, path: str | None = None) -> str | None:
        """Optional JSONL checkpoint of version heads for fast multi-worker warm load."""
        import json
        import os
        from pathlib import Path

        target = Path(
            path
            or os.environ.get(
                "ADOS_VERSION_HEADS",
                str(Path.home() / ".ados" / "version_heads.jsonl"),
            )
        )
        if os.environ.get("ADOS_EVENT_STORE_MEMORY", "").lower() in {"1", "true", "yes"}:
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            lines = [json.dumps(ent.to_dict(), default=str) for ent in self._heads.values()]
        target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return str(target)

    def load_checkpoint(self, path: str | None = None) -> int:
        """Load heads checkpoint if present (then replay may still advance)."""
        import json
        import os
        from pathlib import Path

        from platform_state.entity import CanonicalEntity

        target = Path(
            path
            or os.environ.get(
                "ADOS_VERSION_HEADS",
                str(Path.home() / ".ados" / "version_heads.jsonl"),
            )
        )
        if not target.exists():
            return 0
        loaded = 0
        with self._lock:
            for line in target.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    ent = CanonicalEntity.from_dict(json.loads(line))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
                self._heads[self.key(ent.entity_type, ent.id)] = ent
                loaded += 1
        return loaded

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "heads": len(self._heads),
                "history_streams": len(self._history),
                "ha": "event_store_replay + optional_heads_checkpoint",
            }


version_engine = VersionEngine()
