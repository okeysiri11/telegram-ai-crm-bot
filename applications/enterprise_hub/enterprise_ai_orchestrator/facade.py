"""Enterprise AI Orchestrator Suite — Sprint 24.0 / v7.0.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_ai_orchestrator.facade import EnterpriseAIOrchestratorLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseAIOrchestratorSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = EnterpriseAIOrchestratorLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = EnterpriseAIOrchestratorLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eao_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eao_bootstraps.save(bid, record)
        for agent in full["agents"]:
            aid = agent["agent_id"]
            self.store.eao_agents.save(aid, {**agent, "created_at": _now()})
        did = _id("eao_dec")
        self.store.eao_decisions.save(did, {"decision_id": did, **full["decision"], "created_at": _now()})
        cid = _id("eao_cnf")
        self.store.eao_conflicts.save(cid, {"conflict_id": cid, **full["conflicts"], "created_at": _now()})
        oid = _id("eao_own")
        self.store.eao_owner.save(oid, {"owner_id": oid, **full["owner"], "created_at": _now()})
        record["decision_id"] = did
        self.store.eao_bootstraps.save(bid, record)
        return record

    def register_agent(self, **kwargs: Any) -> dict[str, Any]:
        try:
            agent = self.library.registry.add_agent(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.eao_agents.save(agent["agent_id"], {**agent, "created_at": _now()})
        return agent

    def list_agents(self) -> dict[str, Any]:
        stored = self.store.eao_agents.list_all()
        if not stored:
            stored = self.library.registry.seed_council()
            for a in stored:
                self.store.eao_agents.save(a["agent_id"], {**a, "created_at": _now()})
        return {"agents": stored, "count": len(stored), "extensible": True}

    def convene(self, *, problem: str, required_roles: list[str] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        agents_payload = self.list_agents()["agents"]
        # sync into library registry for selection
        for a in agents_payload:
            if not self.library.registry.get(a["agent_id"]):
                try:
                    self.library.registry.register(
                        agent_id=a["agent_id"],
                        role=a.get("role", "expert"),
                        competencies=a.get("competencies"),
                        access_level=a.get("access_level", "council"),
                        status=a.get("status", "active"),
                    )
                except ValueError:
                    pass
        try:
            selected = self.library.orchestrator.select_agents(
                registry_agents=self.library.registry.list_agents(status="active") or agents_payload,
                required_roles=required_roles,
            )
            if not selected:
                selected = agents_payload
            deliberation = self.library.council.deliberate(problem=problem, agents=selected, context=context)
            orch = self.library.orchestrator.run(problem=problem, agents=selected, council_result=deliberation)
            conflicts = self.library.conflict.resolve(
                contradictions=orch["contradictions"],
                opinions=deliberation["opinions"],
            )
            decision = self.library.decision.compose(
                problem=problem,
                analysis="multi_agent_council",
                opinions=deliberation["opinions"],
                contradictions=orch["contradictions"],
                risks=["misalignment"] if conflicts["has_conflict"] else [],
                benefits=["consolidated_brief"],
                forecast="owner_guided_outcome",
                action_plan=["owner_review"],
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        did = _id("eao_dec")
        record = {
            "decision_id": did,
            "deliberation": deliberation,
            "orchestration": orch,
            "conflicts": conflicts,
            "decision": decision,
            "ai_may_act": False,
            "requires_owner_approval": True,
            "created_at": _now(),
        }
        self.store.eao_decisions.save(did, record)
        cid = _id("eao_cnf")
        self.store.eao_conflicts.save(cid, {"conflict_id": cid, **conflicts, "decision_id": did})
        for a in selected:
            try:
                self.library.registry.record_decision(a["agent_id"], did)
                self.library.memory.remember(agent_id=a["agent_id"], consultation=problem, decision_id=did)
            except ValueError:
                pass
            mid = _id("eao_mem")
            self.store.eao_memory.save(
                mid,
                {"memory_id": mid, "agent_id": a.get("agent_id"), "decision_id": did, "created_at": _now()},
            )
        return record

    def learn(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.learning.learn_from_release(**kwargs)
        lid = _id("eao_learn")
        record = {"learning_id": lid, **result, "created_at": _now()}
        self.store.eao_learning.save(lid, record)
        return record

    def owner_decide(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner_center.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        decision_id = kwargs.get("decision_id", "")
        existing = self.store.eao_decisions.get(decision_id) if decision_id else None
        if decision_id and not existing:
            raise NotFoundError(f"decision not found: {decision_id}")
        oid = _id("eao_own")
        record = {"owner_record_id": oid, **result, "created_at": _now()}
        self.store.eao_owner.save(oid, record)
        if existing:
            existing = {**existing, "owner_decision": result, "updated_at": _now()}
            self.store.eao_decisions.save(decision_id, existing)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eao_bootstraps.list_all()),
            "agents": len(self.store.eao_agents.list_all()),
            "decisions": len(self.store.eao_decisions.list_all()),
            "platform_version": "7.0.0",
        }


enterprise_ai_orchestrator = EnterpriseAIOrchestratorSuite()
