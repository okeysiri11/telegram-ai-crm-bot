"""Context policies — permissions, filtering, visibility, sensitivity, expiration, isolation."""

from __future__ import annotations

import time
from typing import Any

from platform_memory.runtime_models import (
    ContextFragment,
    ContextPermission,
    SensitivityLevel,
    Visibility,
    new_id,
)

_SENSITIVITY_RANK = {
    SensitivityLevel.PUBLIC: 0,
    SensitivityLevel.INTERNAL: 1,
    SensitivityLevel.CONFIDENTIAL: 2,
    SensitivityLevel.RESTRICTED: 3,
}


class ContextPolicyEngine:
    def __init__(self) -> None:
        self._permissions: list[ContextPermission] = []
        self._policy_version = 1

    def reset(self) -> None:
        self._permissions.clear()
        self._policy_version = 1

    def ensure_defaults(self) -> None:
        if self._permissions:
            return
        for source in (
            "user_profile",
            "organization",
            "project",
            "workspace",
            "documents",
            "knowledge_base",
            "workflow_state",
            "conversation_history",
            "agent_memory",
            "runtime_variables",
        ):
            self._permissions.append(
                ContextPermission(
                    permission_id=new_id("cperm"),
                    principal="*",
                    source=source,
                    action="read",
                    max_sensitivity=SensitivityLevel.CONFIDENTIAL,
                )
            )
        self._permissions.append(
            ContextPermission(
                permission_id=new_id("cperm"),
                principal="readonly",
                source="*",
                action="read",
                max_sensitivity=SensitivityLevel.INTERNAL,
            )
        )

    def grant(self, body: dict[str, Any]) -> ContextPermission:
        perm = ContextPermission(
            permission_id=str(body.get("permission_id") or new_id("cperm")),
            principal=str(body.get("principal") or "*"),
            source=str(body.get("source") or "*"),
            action=str(body.get("action") or "read"),
            max_sensitivity=SensitivityLevel(body.get("max_sensitivity") or "internal"),
            isolation_key=body.get("isolation_key"),
            version=int(body.get("version") or self._policy_version),
        )
        self._permissions.append(perm)
        return perm

    def list_permissions(self) -> list[ContextPermission]:
        self.ensure_defaults()
        return list(self._permissions)

    def bump_version(self) -> int:
        self._policy_version += 1
        return self._policy_version

    @property
    def version(self) -> int:
        return self._policy_version

    def _allowed(
        self,
        fragment: ContextFragment,
        *,
        principal: str,
        isolation_key: str | None,
    ) -> bool:
        self.ensure_defaults()
        source = fragment.source.value if hasattr(fragment.source, "value") else str(fragment.source)
        sens = fragment.sensitivity if isinstance(fragment.sensitivity, SensitivityLevel) else SensitivityLevel(fragment.sensitivity)

        matching = [
            p
            for p in self._permissions
            if (p.principal in ("*", principal) and p.source in ("*", source))
        ]
        if not matching:
            return False
        if any(p.action == "deny" for p in matching):
            return False
        max_rank = max(
            _SENSITIVITY_RANK.get(
                p.max_sensitivity if isinstance(p.max_sensitivity, SensitivityLevel) else SensitivityLevel(p.max_sensitivity),
                1,
            )
            for p in matching
        )
        if _SENSITIVITY_RANK.get(sens, 1) > max_rank:
            return False
        if isolation_key:
            frag_iso = fragment.metadata.get("isolation_key")
            if frag_iso and frag_iso != isolation_key:
                return False
            for p in matching:
                if p.isolation_key and p.isolation_key != isolation_key:
                    return False
        return True

    def filter_fragments(
        self,
        fragments: list[ContextFragment],
        *,
        principal: str = "system",
        isolation_key: str | None = None,
        max_sensitivity: str | None = None,
        now: float | None = None,
    ) -> tuple[list[ContextFragment], int]:
        """Return (kept, filtered_count)."""
        now = now if now is not None else time.time()
        kept: list[ContextFragment] = []
        filtered = 0
        max_sens = SensitivityLevel(max_sensitivity) if max_sensitivity else None
        for frag in fragments:
            if frag.expires_at is not None and frag.expires_at < now:
                filtered += 1
                continue
            if max_sens is not None:
                sens = frag.sensitivity if isinstance(frag.sensitivity, SensitivityLevel) else SensitivityLevel(frag.sensitivity)
                if _SENSITIVITY_RANK.get(sens, 1) > _SENSITIVITY_RANK.get(max_sens, 1):
                    filtered += 1
                    continue
            vis = frag.visibility if isinstance(frag.visibility, Visibility) else Visibility(frag.visibility)
            if vis == Visibility.USER and frag.metadata.get("user_id") and frag.metadata.get("user_id") != principal:
                # principal may be user_id
                if principal not in ("system", "*", frag.metadata.get("user_id")):
                    filtered += 1
                    continue
            if not self._allowed(frag, principal=principal, isolation_key=isolation_key):
                filtered += 1
                continue
            kept.append(frag)
        return kept, filtered


policy_engine = ContextPolicyEngine()
