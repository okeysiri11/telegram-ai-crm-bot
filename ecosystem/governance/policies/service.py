# Policy engine — create/update policies across governance domains.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.governance.events import PolicyCreatedEvent, PolicyUpdatedEvent
from ecosystem.governance.models import GovernanceDomain, Policy, PolicyStatus
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


BUILTIN_POLICIES: list[tuple[str, GovernanceDomain, list[str], int]] = [
    ("Platform Access Control", GovernanceDomain.PLATFORM, ["require_auth", "rbac_enforced"], 730),
    ("Application Change Control", GovernanceDomain.APPLICATION, ["versioned_releases", "approval_for_prod"], 365),
    ("Agent Accountability", GovernanceDomain.AGENT, ["audit_agent_actions", "human_escalation"], 365),
    ("Workflow Integrity", GovernanceDomain.WORKFLOW, ["idempotent_steps", "dead_letter_handling"], 365),
    ("Data Retention", GovernanceDomain.DATA, ["retain_365d", "purge_on_request"], 365),
    ("Knowledge Provenance", GovernanceDomain.KNOWLEDGE, ["source_attribution", "review_stale_nodes"], 180),
]


class PolicyService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._seed()

    def _seed(self) -> None:
        if self._store.policies.count() > 0:
            return
        for name, domain, rules, retention in BUILTIN_POLICIES:
            policy = Policy(name=name, domain=domain, rules=rules, retention_days=retention, description=f"Builtin {domain.value} policy")
            self._store.policies.save(policy.policy_id, policy)

    def _ensure_seeded(self) -> None:
        if self._store.policies.count() == 0:
            self._seed()

    async def create(
        self,
        name: str,
        domain: GovernanceDomain,
        *,
        description: str = "",
        rules: list[str] | None = None,
        retention_days: int = 365,
    ) -> Policy:
        if not name:
            raise ValidationError("name is required")
        self._ensure_seeded()
        policy = Policy(
            name=name,
            domain=domain,
            description=description,
            rules=rules or [],
            retention_days=retention_days,
        )
        self._store.policies.save(policy.policy_id, policy)
        await publish(PolicyCreatedEvent(policy_id=policy.policy_id, name=name, domain=domain.value))
        return policy

    async def update(self, policy_id: str, **fields: Any) -> Policy:
        policy = self.get(policy_id)
        for key in ("name", "description", "retention_days"):
            if key in fields and fields[key] is not None:
                setattr(policy, key, fields[key])
        if "rules" in fields and fields["rules"] is not None:
            policy.rules = list(fields["rules"])
        if "status" in fields and fields["status"] is not None:
            policy.status = PolicyStatus(fields["status"]) if isinstance(fields["status"], str) else fields["status"]
        # bump version
        major, _, minor = policy.version.partition(".")
        try:
            policy.version = f"{major}.{int(minor or 0) + 1}"
        except ValueError:
            policy.version = f"{policy.version}.1"
        policy.updated_at = time.time()
        self._store.policies.save(policy_id, policy)
        await publish(PolicyUpdatedEvent(policy_id=policy_id, name=policy.name, version=policy.version))
        return policy

    def get(self, policy_id: str) -> Policy:
        self._ensure_seeded()
        policy = self._store.policies.get(policy_id)
        if policy is None:
            raise NotFoundError("Policy", policy_id)
        return policy

    def list_policies(self, *, domain: GovernanceDomain | None = None) -> list[Policy]:
        self._ensure_seeded()
        policies = self._store.policies.list_all()
        if domain:
            policies = [p for p in policies if p.domain == domain]
        return policies

    def active_rules(self, domain: GovernanceDomain) -> list[str]:
        rules: list[str] = []
        for policy in self.list_policies(domain=domain):
            if policy.status == PolicyStatus.ACTIVE:
                rules.extend(policy.rules)
        return rules


policy_service = PolicyService()
