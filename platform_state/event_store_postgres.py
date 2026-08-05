"""Optional Postgres backend for PlatformEventStore — Sprint 35.1.

Selected via ADOS_EVENT_STORE_BACKEND=postgres. Public Event Store API unchanged.
Default remains JSONL.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def postgres_enabled() -> bool:
    return os.environ.get("ADOS_EVENT_STORE_BACKEND", "jsonl").lower() in {
        "postgres",
        "postgresql",
        "pg",
    }


def _engine():
    from sqlalchemy import create_engine

    url = os.environ.get("DATABASE_URL") or os.environ.get("ADOS_DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL required for postgres event store backend")
    # Ensure sync driver
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)


def pg_append(row: dict[str, Any]) -> int:
    from sqlalchemy import text

    eng = _engine()
    with eng.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO platform_state_events (
                    event_id, event_type, entity_type, entity_id,
                    workspace_id, tenant_id, change_id, version,
                    actor_id, source_client, agent_id,
                    payload_json, before_json, after_json,
                    occurred_at, stream_key
                ) VALUES (
                    :event_id, :event_type, :entity_type, :entity_id,
                    :workspace_id, :tenant_id, :change_id, :version,
                    :actor_id, :source_client, :agent_id,
                    CAST(:payload_json AS jsonb),
                    CAST(:before_json AS jsonb),
                    CAST(:after_json AS jsonb),
                    :occurred_at, :stream_key
                )
                ON CONFLICT (event_id) DO NOTHING
                RETURNING seq
                """
            ),
            {
                **row,
                "payload_json": json.dumps(row.get("payload") or {}, default=str),
                "before_json": json.dumps(row.get("before"), default=str) if row.get("before") is not None else None,
                "after_json": json.dumps(row.get("after"), default=str) if row.get("after") is not None else None,
            },
        )
        seq = result.scalar()
        if seq is None:
            existing = conn.execute(
                text("SELECT seq FROM platform_state_events WHERE event_id = :event_id"),
                {"event_id": row["event_id"]},
            ).scalar()
            return int(existing or 0)
        return int(seq)


def pg_since_seq(after_seq: int = 0, *, limit: int = 10_000) -> list[dict[str, Any]]:
    from sqlalchemy import text

    eng = _engine()
    with eng.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT * FROM platform_state_events
                WHERE seq > :after_seq
                ORDER BY seq ASC
                LIMIT :limit
                """
            ),
            {"after_seq": after_seq, "limit": limit},
        ).mappings()
        return [_row_to_dict(r) for r in rows]


def _row_to_dict(r: Any) -> dict[str, Any]:
    payload = r["payload_json"]
    before = r["before_json"]
    after = r["after_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    if isinstance(before, str):
        before = json.loads(before)
    if isinstance(after, str):
        after = json.loads(after)
    return {
        "seq": int(r["seq"]),
        "event_id": r["event_id"],
        "event_type": r["event_type"],
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "workspace_id": r["workspace_id"],
        "tenant_id": r["tenant_id"],
        "change_id": r["change_id"],
        "version": int(r["version"] or 1),
        "actor_id": r["actor_id"],
        "source_client": r["source_client"],
        "payload": payload or {},
        "before": before,
        "after": after,
        "occurred_at": r["occurred_at"],
        "stream_key": r["stream_key"],
        "agent_id": r["agent_id"],
    }


def pg_safe_append(row: dict[str, Any]) -> int | None:
    try:
        return pg_append(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("postgres event store append failed: %s", exc)
        return None
