"""Conflict Resolution Engine — Sprint 34.2D.

Strategies: last_write_wins | manual_review | field_merge | business_rule | version_reject
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Callable

from platform_state.models import EntityMeta, utcnow


class MergeStrategy(str, enum.Enum):
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL_REVIEW = "manual_review"
    FIELD_MERGE = "field_merge"
    BUSINESS_RULE = "business_rule"
    VERSION_REJECT = "version_reject"


@dataclass
class ConflictResult:
    resolved: bool
    winner: dict[str, Any]
    strategy: str
    message: str
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    requires_manual_review: bool = False
    merged_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved": self.resolved,
            "winner": self.winner,
            "strategy": self.strategy,
            "message": self.message,
            "conflicts": self.conflicts,
            "requires_manual_review": self.requires_manual_review,
            "merged_fields": self.merged_fields,
        }


BusinessRuleFn = Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], dict[str, Any] | None]


class ConflictResolutionEngine:
    def __init__(self) -> None:
        self._pending_review: list[dict[str, Any]] = []
        self._business_rules: dict[str, BusinessRuleFn] = {}
        self._conflict_count = 0

    def register_business_rule(self, entity_type: str, fn: BusinessRuleFn) -> None:
        self._business_rules[entity_type] = fn

    @property
    def conflict_count(self) -> int:
        return self._conflict_count

    def pending_reviews(self) -> list[dict[str, Any]]:
        return list(self._pending_review)

    def detect(
        self,
        *,
        server: EntityMeta,
        incoming_version: int,
        incoming_payload: dict[str, Any],
        server_payload: dict[str, Any],
        incoming_updated_at: str | None = None,
        incoming_source: str | None = None,
        server_source: str | None = None,
    ) -> bool:
        if incoming_version < server.version:
            return True
        if incoming_version == server.version and incoming_updated_at and incoming_updated_at != server.updated_at:
            # Concurrent same-version edits from different clients
            if incoming_source and server_source and incoming_source != server_source:
                return True
            if incoming_updated_at < server.updated_at:
                return True
        return False

    def resolve(
        self,
        *,
        server: EntityMeta,
        incoming_version: int,
        incoming_payload: dict[str, Any],
        server_payload: dict[str, Any],
        incoming_updated_at: str | None = None,
        strategy: MergeStrategy | str = MergeStrategy.VERSION_REJECT,
        merge_fields: list[str] | None = None,
        entity_type: str | None = None,
        incoming_source: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ConflictResult:
        strat = MergeStrategy(strategy) if not isinstance(strategy, MergeStrategy) else strategy
        has_conflict = self.detect(
            server=server,
            incoming_version=incoming_version,
            incoming_payload=incoming_payload,
            server_payload=server_payload,
            incoming_updated_at=incoming_updated_at,
            incoming_source=incoming_source,
            server_source=server.source_client,
        )

        if not has_conflict and incoming_version >= server.version:
            return ConflictResult(
                resolved=True,
                winner=incoming_payload,
                strategy="accept_incoming",
                message="accepted",
            )

        self._conflict_count += 1

        if strat == MergeStrategy.VERSION_REJECT:
            return ConflictResult(
                resolved=False,
                winner=server_payload,
                strategy=strat.value,
                message=f"stale version {incoming_version} < server {server.version}",
                conflicts=[{"field": "version", "server": server.version, "incoming": incoming_version}],
            )

        if strat == MergeStrategy.LAST_WRITE_WINS:
            incoming_ts = incoming_updated_at or ""
            server_ts = server.updated_at or ""
            if incoming_ts >= server_ts:
                return ConflictResult(
                    resolved=True,
                    winner=incoming_payload,
                    strategy=strat.value,
                    message="last write wins — incoming",
                )
            return ConflictResult(
                resolved=True,
                winner=server_payload,
                strategy=strat.value,
                message="last write wins — server",
            )

        if strat == MergeStrategy.FIELD_MERGE:
            merged = dict(server_payload)
            changed: list[str] = []
            fields = merge_fields or sorted(
                set(incoming_payload.keys()) | set(server_payload.keys())
            )
            field_conflicts: list[dict[str, Any]] = []
            for f in fields:
                if f in {"id", "entity_type", "version", "change_id"}:
                    continue
                s_val = server_payload.get(f)
                i_val = incoming_payload.get(f)
                if s_val == i_val:
                    continue
                if s_val is None:
                    merged[f] = i_val
                    changed.append(f)
                elif i_val is None:
                    continue
                else:
                    # Prefer incoming for scalar; nest-merge for dicts
                    if isinstance(s_val, dict) and isinstance(i_val, dict):
                        nested = {**s_val, **i_val}
                        merged[f] = nested
                        changed.append(f)
                    else:
                        field_conflicts.append({"field": f, "server": s_val, "incoming": i_val})
                        merged[f] = i_val
                        changed.append(f)
            return ConflictResult(
                resolved=True,
                winner=merged,
                strategy=strat.value,
                message="field merge applied",
                conflicts=field_conflicts,
                merged_fields=changed,
            )

        if strat == MergeStrategy.BUSINESS_RULE:
            et = entity_type or str(server.entity_type)
            rule = self._business_rules.get(et)
            if rule is None:
                return ConflictResult(
                    resolved=False,
                    winner=server_payload,
                    strategy=strat.value,
                    message=f"no business rule for {et}",
                    requires_manual_review=True,
                )
            winner = rule(server_payload, incoming_payload, context or {})
            if winner is None:
                return ConflictResult(
                    resolved=False,
                    winner=server_payload,
                    strategy=strat.value,
                    message="business rule deferred to manual review",
                    requires_manual_review=True,
                )
            return ConflictResult(
                resolved=True,
                winner=winner,
                strategy=strat.value,
                message="business rule merge",
            )

        # MANUAL_REVIEW
        ticket = {
            "id": f"cfl-{self._conflict_count}",
            "at": utcnow().isoformat(),
            "entity_type": server.entity_type,
            "entity_id": server.entity_id,
            "server": server_payload,
            "incoming": incoming_payload,
            "incoming_version": incoming_version,
            "server_version": server.version,
            "incoming_source": incoming_source,
            "server_source": server.source_client,
        }
        self._pending_review.append(ticket)
        return ConflictResult(
            resolved=False,
            winner=server_payload,
            strategy=strat.value,
            message="queued for manual review",
            requires_manual_review=True,
            conflicts=[ticket],
        )

    def resolve_manual(self, conflict_id: str, winner: dict[str, Any]) -> ConflictResult:
        remaining = []
        found = None
        for item in self._pending_review:
            if item["id"] == conflict_id:
                found = item
            else:
                remaining.append(item)
        self._pending_review = remaining
        if found is None:
            return ConflictResult(
                resolved=False,
                winner={},
                strategy=MergeStrategy.MANUAL_REVIEW.value,
                message="conflict not found",
            )
        return ConflictResult(
            resolved=True,
            winner=winner,
            strategy=MergeStrategy.MANUAL_REVIEW.value,
            message=f"manual resolution of {conflict_id}",
        )

    def reset(self) -> None:
        self._pending_review.clear()
        self._conflict_count = 0


conflict_engine = ConflictResolutionEngine()


# 34.2C compatibility facade
class ConflictResolver:
    def resolve(self, **kwargs: Any) -> ConflictResult:
        result = conflict_engine.resolve(strategy=MergeStrategy.VERSION_REJECT, **kwargs)
        if not result.resolved and result.strategy == MergeStrategy.VERSION_REJECT.value:
            return ConflictResult(
                resolved=False,
                winner=result.winner,
                strategy="reject_stale",
                message=result.message,
                conflicts=result.conflicts,
                requires_manual_review=result.requires_manual_review,
                merged_fields=result.merged_fields,
            )
        if result.resolved and result.strategy == "accept_incoming":
            return result
        if result.resolved:
            return ConflictResult(
                resolved=True,
                winner=result.winner,
                strategy="accept_incoming",
                message=result.message,
            )
        return result


conflict_resolver = ConflictResolver()
