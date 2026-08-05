"""PlatformTransaction — atomic cross-module operations (Sprint 34.2D)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from platform_state.models import utcnow

logger = logging.getLogger(__name__)

OpFn = Callable[[], Awaitable[Any] | Any]
UndoFn = Callable[[], Awaitable[None] | None]


@dataclass
class TxOperation:
    name: str
    run: OpFn
    undo: UndoFn | None = None
    result: Any = None


@dataclass
class PlatformTransaction:
    """
    Collects operations; commit applies all then publishes; rollback undoes applied ops.
    """

    tx_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str | None = None
    tenant_id: str | None = None
    actor_id: str | None = None
    source_client: str | None = None
    _ops: list[TxOperation] = field(default_factory=list)
    _applied: list[TxOperation] = field(default_factory=list)
    _committed: bool = False
    _aborted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def add(
        self,
        name: str,
        run: OpFn,
        *,
        undo: UndoFn | None = None,
    ) -> PlatformTransaction:
        if self._committed or self._aborted:
            raise RuntimeError("transaction already finished")
        self._ops.append(TxOperation(name=name, run=run, undo=undo))
        return self

    async def commit(self) -> dict[str, Any]:
        if self._committed:
            raise RuntimeError("already committed")
        if self._aborted:
            raise RuntimeError("already aborted")
        results: dict[str, Any] = {}
        try:
            for op in self._ops:
                result = op.run()
                if hasattr(result, "__await__"):
                    result = await result  # type: ignore[misc]
                op.result = result
                self._applied.append(op)
                results[op.name] = result
            self._committed = True
            return {
                "tx_id": self.tx_id,
                "status": "committed",
                "at": utcnow().isoformat(),
                "results": results,
                "ops": [o.name for o in self._applied],
            }
        except Exception as exc:
            logger.exception("platform_transaction_failed tx_id=%s", self.tx_id)
            await self.rollback()
            return {
                "tx_id": self.tx_id,
                "status": "rolled_back",
                "error": str(exc),
                "at": utcnow().isoformat(),
                "ops_applied_before_failure": [o.name for o in self._applied],
            }

    async def rollback(self) -> dict[str, Any]:
        self._aborted = True
        undone: list[str] = []
        for op in reversed(self._applied):
            if op.undo is None:
                continue
            try:
                result = op.undo()
                if hasattr(result, "__await__"):
                    await result  # type: ignore[misc]
                undone.append(op.name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("tx undo failed op=%s err=%s", op.name, exc)
        self._applied.clear()
        return {"tx_id": self.tx_id, "status": "rolled_back", "undone": undone}


def begin_transaction(
    *,
    workspace_id: str | None = None,
    tenant_id: str | None = None,
    actor_id: str | None = None,
    source_client: str | None = None,
) -> PlatformTransaction:
    return PlatformTransaction(
        workspace_id=workspace_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        source_client=source_client,
    )
