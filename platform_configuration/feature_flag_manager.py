# FeatureFlagManager — feature toggles, rollout, and scoped configuration.

from __future__ import annotations

import hashlib
import logging
from typing import Any

from platform_configuration.models import FeatureFlag

logger = logging.getLogger(__name__)


class FeatureFlagManager:
    """Enable/disable features with gradual rollout and scoped targeting."""

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def reset(self) -> None:
        self._flags.clear()

    def register(self, flag: FeatureFlag) -> FeatureFlag:
        self._flags[flag.key] = flag
        return flag

    def set(
        self,
        key: str,
        *,
        enabled: bool = True,
        rollout_percent: float = 100.0,
        experimental: bool = False,
    ) -> FeatureFlag:
        flag = self._flags.get(key) or FeatureFlag(key=key)
        flag.enabled = enabled
        flag.rollout_percent = max(0.0, min(100.0, rollout_percent))
        flag.experimental = experimental
        self._flags[key] = flag
        return flag

    def scope_agent(self, key: str, agent_id: str, *, enabled: bool = True) -> None:
        flag = self._flags.setdefault(key, FeatureFlag(key=key))
        if enabled:
            flag.agent_ids.add(agent_id)
        else:
            flag.agent_ids.discard(agent_id)

    def scope_workflow(self, key: str, workflow_id: str, *, enabled: bool = True) -> None:
        flag = self._flags.setdefault(key, FeatureFlag(key=key))
        if enabled:
            flag.workflow_ids.add(workflow_id)
        else:
            flag.workflow_ids.discard(workflow_id)

    def scope_user(self, key: str, user_id: str, *, enabled: bool = True) -> None:
        flag = self._flags.setdefault(key, FeatureFlag(key=key))
        if enabled:
            flag.user_ids.add(user_id)
        else:
            flag.user_ids.discard(user_id)

    def is_enabled(
        self,
        key: str,
        *,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        user_id: str | None = None,
        default: bool = False,
    ) -> bool:
        flag = self._flags.get(key)
        if flag is None:
            return default
        if not flag.enabled:
            return False

        if flag.agent_ids and agent_id and agent_id not in flag.agent_ids:
            return False
        if flag.workflow_ids and workflow_id and workflow_id not in flag.workflow_ids:
            return False
        if flag.user_ids and user_id and user_id not in flag.user_ids:
            return False

        if flag.rollout_percent >= 100.0:
            return True
        if flag.rollout_percent <= 0.0:
            return False

        subject = user_id or agent_id or workflow_id or key
        bucket = int(hashlib.sha256(f"{key}:{subject}".encode()).hexdigest(), 16) % 100
        return bucket < flag.rollout_percent

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._flags.items()}


feature_flag_manager = FeatureFlagManager()
