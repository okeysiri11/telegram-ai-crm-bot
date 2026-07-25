"""Enterprise Multi-Agent OS library — Sprint 27.1."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_ai_os.models import (
    API_PREFIX,
    ARCHITECTURE,
    BUS_MESSAGE_TYPES,
    COLLABORATION_ACTIONS,
    KPI_TARGETS,
    MAOS_PREFIX,
    MEMORY_LAYERS,
    ORCHESTRATOR_MODES,
    PRINCIPLES,
    SPRINT,
    VERSION,
    WEB_PATH,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    role: str
    status: str = "idle"
    load: float = 0.0
    capabilities: list[str] = field(default_factory=list)
    cost_per_1k: float = 0.002
    speed_tps: float = 40.0
    memory_mb: float = 512.0
    models: list[str] = field(default_factory=list)


class MultiAgentOSLibrary:
    """Executive AI layer over the enterprise agent fleet."""

    def __init__(self) -> None:
        self._agents = self._seed_agents()
        self._bus: deque[dict[str, Any]] = deque(maxlen=500)
        self._priority_queue: list[dict[str, Any]] = []
        self._tasks: dict[str, dict[str, Any]] = {}
        self._memory: dict[str, list[dict[str, Any]]] = {layer: [] for layer in MEMORY_LAYERS}
        self._task_history: list[dict[str, Any]] = []
        self._errors: list[dict[str, Any]] = []
        self._cost_total = 0.0
        self._latencies: list[float] = []

    def _seed_agents(self) -> dict[str, AgentRecord]:
        specs = [
            ("director", "AI Director", "executive", ["plan", "delegate", "merge", "supervise"], 0.01, 20.0, ["gpt-executive"]),
            ("sales", "Sales Agent", "sales", ["qualify", "negotiate", "crm"], 0.003, 50.0, ["gpt-sales"]),
            ("ops", "Ops Copilot", "operations", ["triage", "workflow", "report"], 0.002, 55.0, ["gpt-ops"]),
            ("legal", "Legal Case Agent", "legal", ["review", "compliance", "draft"], 0.004, 35.0, ["gpt-legal"]),
            ("finance", "Finance CFO Agent", "finance", ["invoice", "forecast", "treasury"], 0.004, 35.0, ["gpt-cfo"]),
            ("research", "Research Agent", "knowledge", ["search", "summarize", "rag"], 0.002, 60.0, ["gpt-research", "embed-v1"]),
            ("critic", "Critic Agent", "quality", ["critique", "score", "vote"], 0.002, 70.0, ["gpt-critic"]),
            ("builder", "Builder Agent", "engineering", ["codegen", "test", "refactor"], 0.005, 30.0, ["gpt-code"]),
        ]
        agents = {}
        for code, name, role, caps, cost, speed, models in specs:
            aid = f"agent_{code}"
            agents[aid] = AgentRecord(
                agent_id=aid,
                name=name,
                role=role,
                capabilities=caps,
                cost_per_1k=cost,
                speed_tps=speed,
                models=models,
                memory_mb=256 if code != "director" else 1024,
            )
        return agents

    # —— inventory / status ——
    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def inventory(self) -> dict[str, Any]:
        return {
            "architecture": list(ARCHITECTURE),
            "architecture_count": len(ARCHITECTURE),
            "bus_message_types": list(BUS_MESSAGE_TYPES),
            "orchestrator_modes": list(ORCHESTRATOR_MODES),
            "memory_layers": list(MEMORY_LAYERS),
            "collaboration_actions": list(COLLABORATION_ACTIONS),
            "agent_count": len(self._agents),
            "version": VERSION,
            "sprint": SPRINT,
            "api_prefix": API_PREFIX,
            "maos_prefix": MAOS_PREFIX,
            "path": WEB_PATH,
            "passed": True,
        }

    # —— 1. Executive AI ——
    def executive_submit(self, goal: str, *, priority: int = 5) -> dict[str, Any]:
        """Accept a goal, decompose, assign executors, run, merge results."""
        t0 = time.perf_counter()
        task_id = _id("exec")
        subtasks = self._decompose(goal)
        assignments = []
        for st in subtasks:
            agent = self._select_executor(st["capability"])
            if agent:
                agent.status = "busy"
                agent.load = min(1.0, agent.load + 0.25)
                assignments.append({"subtask": st["id"], "agent_id": agent.agent_id, "name": agent.name})
                self.bus_publish(
                    "request",
                    sender="agent_director",
                    recipient=agent.agent_id,
                    payload={"task": st, "goal": goal},
                    priority=priority,
                )
        results = []
        for asg in assignments:
            agent = self._agents[asg["agent_id"]]
            piece = {
                "subtask": asg["subtask"],
                "agent_id": agent.agent_id,
                "output": f"{agent.name} completed '{asg['subtask']}' for goal",
                "ok": True,
            }
            results.append(piece)
            self.bus_publish(
                "response",
                sender=agent.agent_id,
                recipient="agent_director",
                payload=piece,
                priority=priority,
            )
            agent.status = "idle"
            agent.load = max(0.0, agent.load - 0.25)
            self._cost_total += agent.cost_per_1k

        merged = self._merge_results(goal, results)
        elapsed = (time.perf_counter() - t0) * 1000
        self._latencies.append(elapsed)
        record = {
            "task_id": task_id,
            "goal": goal,
            "priority": priority,
            "subtasks": subtasks,
            "assignments": assignments,
            "results": results,
            "merged": merged,
            "elapsed_ms": round(elapsed, 3),
            "status": "completed",
            "controlled": True,
            "at": _now(),
        }
        self._tasks[task_id] = record
        self._task_history.append(record)
        return record

    def _decompose(self, goal: str) -> list[dict[str, Any]]:
        g = goal.lower()
        plan = [{"id": "analyze", "capability": "plan", "title": "Analyze goal"}]
        if any(k in g for k in ("sale", "lead", "crm", "client")):
            plan.append({"id": "sales_work", "capability": "crm", "title": "Sales execution"})
        if any(k in g for k in ("invoice", "finance", "budget")):
            plan.append({"id": "finance_work", "capability": "invoice", "title": "Finance execution"})
        if any(k in g for k in ("legal", "contract", "compliance")):
            plan.append({"id": "legal_work", "capability": "review", "title": "Legal review"})
        if any(k in g for k in ("research", "knowledge", "doc")):
            plan.append({"id": "research_work", "capability": "search", "title": "Knowledge research"})
        if len(plan) == 1:
            plan.append({"id": "ops_work", "capability": "workflow", "title": "Ops execution"})
        plan.append({"id": "quality", "capability": "critique", "title": "Quality critique"})
        plan.append({"id": "merge", "capability": "merge", "title": "Merge outcomes"})
        return plan

    def _select_executor(self, capability: str) -> AgentRecord | None:
        candidates = [
            a for a in self._agents.values() if capability in a.capabilities and a.status != "offline"
        ]
        if not candidates:
            candidates = [a for a in self._agents.values() if a.role != "executive"]
        if not candidates:
            return None
        return min(candidates, key=lambda a: (a.load, -a.speed_tps, a.cost_per_1k))

    def _merge_results(self, goal: str, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "goal": goal,
            "summary": f"Merged {len(results)} agent outputs",
            "outputs": [r["output"] for r in results],
            "consensus": True,
        }

    # —— 2. Agent Registry 2.0 ——
    def agent_registry(self) -> dict[str, Any]:
        items = []
        for a in self._agents.values():
            items.append(
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "load": round(a.load, 3),
                    "capabilities": list(a.capabilities),
                    "cost": a.cost_per_1k,
                    "speed": a.speed_tps,
                    "memory": a.memory_mb,
                    "models": list(a.models),
                }
            )
        return {"agents": items, "count": len(items), "version": "2.0"}

    # —— 3. Communication Bus ——
    def bus_publish(
        self,
        msg_type: str,
        *,
        sender: str,
        recipient: str | None = None,
        payload: dict[str, Any] | None = None,
        priority: int = 5,
        stream: bool = False,
    ) -> dict[str, Any]:
        if msg_type not in BUS_MESSAGE_TYPES:
            return {"ok": False, "error": "invalid_message_type"}
        msg = {
            "id": _id("msg"),
            "type": msg_type,
            "sender": sender,
            "recipient": recipient,
            "payload": payload or {},
            "priority": priority,
            "stream": stream or msg_type == "stream",
            "at": _now(),
        }
        self._bus.append(msg)
        if priority <= 2:
            self._priority_queue.append(msg)
            self._priority_queue.sort(key=lambda m: m["priority"])
        return {"ok": True, "message": msg}

    def bus_status(self) -> dict[str, Any]:
        by_type: dict[str, int] = defaultdict(int)
        for m in self._bus:
            by_type[m["type"]] += 1
        return {
            "supported": list(BUS_MESSAGE_TYPES),
            "queue_depth": len(self._bus),
            "priority_queue_depth": len(self._priority_queue),
            "by_type": dict(by_type),
            "recent": list(self._bus)[-10:],
        }

    # —— 4. Task Orchestrator ——
    def orchestrate(
        self,
        name: str,
        steps: list[dict[str, Any]] | None = None,
        *,
        mode: str = "sequential",
        timeout_ms: int = 5000,
        retry: int = 1,
        enable_rollback: bool = False,
    ) -> dict[str, Any]:
        execution_modes = {"parallel", "sequential", "conditional"}
        if mode not in execution_modes:
            return {"ok": False, "error": "invalid_mode", "supported": list(execution_modes)}
        dag_id = _id("dag")
        steps = steps or [
            {"id": "s1", "action": "plan", "depends_on": []},
            {"id": "s2", "action": "execute", "depends_on": ["s1"]},
            {"id": "s3", "action": "merge", "depends_on": ["s2"]},
        ]
        t0 = time.perf_counter()
        executed: list[dict[str, Any]] = []
        attempts = 0
        ok = True
        last_error = None
        while attempts <= retry:
            attempts += 1
            try:
                executed = []
                if mode == "parallel":
                    for st in steps:
                        executed.append(self._run_step(st))
                elif mode == "conditional":
                    for st in steps:
                        if st.get("when") is False:
                            executed.append({**st, "skipped": True})
                        else:
                            executed.append(self._run_step(st))
                else:
                    done: set[str] = set()
                    remaining = list(steps)
                    while remaining:
                        progressed = False
                        for st in list(remaining):
                            deps = set(st.get("depends_on") or [])
                            if deps.issubset(done):
                                executed.append(self._run_step(st))
                                done.add(st["id"])
                                remaining.remove(st)
                                progressed = True
                        if not progressed:
                            raise RuntimeError("dag_deadlock")
                elapsed = (time.perf_counter() - t0) * 1000
                if elapsed > timeout_ms:
                    raise TimeoutError("orchestrator_timeout")
                ok = True
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001
                ok = False
                last_error = str(exc)
                self._errors.append({"dag_id": dag_id, "error": str(exc), "at": _now()})
                if attempts > retry:
                    if enable_rollback:
                        executed = [{"rolled_back": True, "reason": str(exc)}]
                    break
        elapsed = (time.perf_counter() - t0) * 1000
        self._latencies.append(elapsed)
        record = {
            "ok": ok,
            "dag_id": dag_id,
            "name": name,
            "mode": mode,
            "steps": steps,
            "executed": executed,
            "attempts": attempts,
            "timeout_ms": timeout_ms,
            "retry": retry,
            "rollback": enable_rollback,
            "error": last_error,
            "elapsed_ms": round(elapsed, 3),
            "policies": list(ORCHESTRATOR_MODES),
            "at": _now(),
        }
        self._task_history.append(record)
        return record

    def _run_step(self, step: dict[str, Any]) -> dict[str, Any]:
        return {"id": step.get("id"), "action": step.get("action"), "status": "ok", "at": _now()}

    # —— 5. Memory Manager ——
    def memory_write(self, layer: str, content: str, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        if layer not in MEMORY_LAYERS:
            return {"ok": False, "error": "invalid_layer"}
        entry = {"id": _id("mem"), "content": content, "meta": meta or {}, "at": _now()}
        self._memory[layer].append(entry)
        self._memory[layer] = self._memory[layer][-100:]
        return {"ok": True, "layer": layer, "entry": entry}

    def memory_read(self, layer: str | None = None) -> dict[str, Any]:
        if layer:
            if layer not in MEMORY_LAYERS:
                return {"ok": False, "error": "invalid_layer"}
            return {"ok": True, "layer": layer, "entries": list(self._memory[layer])}
        return {
            "ok": True,
            "layers": list(MEMORY_LAYERS),
            "counts": {k: len(v) for k, v in self._memory.items()},
            "snapshot": {k: v[-5:] for k, v in self._memory.items()},
        }

    # —— 6. Collaboration ——
    def collaborate(self, topic: str, *, action: str = "discuss", proposals: list[str] | None = None) -> dict[str, Any]:
        if action not in COLLABORATION_ACTIONS:
            return {"ok": False, "error": "invalid_action"}
        proposals = proposals or [
            f"Option A for {topic}",
            f"Option B for {topic}",
            f"Option C for {topic}",
        ]
        participants = [a for a in self._agents.values() if a.role in {"quality", "executive", "operations", "knowledge"}][:4]
        discussion = [{"agent": a.name, "says": f"{a.name} discusses {topic}"} for a in participants]
        votes = {p: 0 for p in proposals}
        for i, a in enumerate(participants):
            choice = proposals[i % len(proposals)]
            votes[choice] += 1
            self.bus_publish("event", sender=a.agent_id, recipient="agent_director", payload={"vote": choice, "topic": topic})
        best = max(votes.items(), key=lambda kv: kv[1])[0]
        critiques = [f"{a.name} critiques weaknesses in weaker options" for a in participants if a.role == "quality"]
        if not critiques:
            critiques = ["Critic Agent critiques weaker options"]
        merged = {"topic": topic, "best": best, "votes": votes, "merged_answer": best}
        return {
            "ok": True,
            "action": action,
            "topic": topic,
            "discussion": discussion if action in {"discuss", "vote", "select_best", "merge"} else [],
            "votes": votes if action in {"vote", "select_best", "merge"} else {},
            "best": best if action in {"select_best", "vote", "merge"} else None,
            "critiques": critiques if action in {"critique", "merge"} else [],
            "merged": merged if action == "merge" else None,
            "participants": [a.agent_id for a in participants],
        }

    # —— 7. Executive Dashboard ——
    def executive_dashboard(self) -> dict[str, Any]:
        active = [a.agent_id for a in self._agents.values() if a.status == "busy"]
        avg_latency = round(sum(self._latencies) / max(len(self._latencies), 1), 3)
        return {
            "title": "AI Executive Dashboard",
            "version": VERSION,
            "active_agents": active,
            "active_count": len(active),
            "agents_total": len(self._agents),
            "queues": {
                "bus": len(self._bus),
                "priority": len(self._priority_queue),
                "tasks": len(self._tasks),
            },
            "load": {a.agent_id: round(a.load, 3) for a in self._agents.values()},
            "cost": round(self._cost_total, 6),
            "latency_ms_avg": avg_latency,
            "errors": self._errors[-10:],
            "task_history": self._task_history[-10:],
            "kpi": dict(KPI_TARGETS),
            "path": WEB_PATH,
            "api_prefix": API_PREFIX,
        }

    def dashboard(self) -> dict[str, Any]:
        return self.executive_dashboard()

    def integrations(self) -> dict[str, Any]:
        return {
            "targets": [
                "enterprise_hub",
                "platform_agents",
                "platform_orchestrator",
                "command_center",
                "navigation",
                "workspace",
                "release_candidate",
            ],
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
        }

    def bootstrap(self) -> dict[str, Any]:
        inv = self.inventory()
        dash = self.executive_dashboard()
        links = self.integrations()
        # warm systems
        self.memory_write("session", "bootstrap session", meta={"sprint": SPRINT})
        self.memory_write("organization", "org memory seed")
        demo = self.executive_submit("Research and prepare weekly ops report")
        collab = self.collaborate("release readiness", action="merge")
        orch = self.orchestrate("demo_dag", mode="sequential")
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "executive_ai_ready": True,
            "agent_registry_ready": True,
            "communication_bus_ready": True,
            "task_orchestrator_ready": True,
            "memory_manager_ready": True,
            "collaboration_ready": True,
            "executive_dashboard_ready": True,
            "version": VERSION,
            "sprint": SPRINT,
            "api_prefix": API_PREFIX,
            "maos_prefix": MAOS_PREFIX,
            "path": WEB_PATH,
            "kpi": dict(KPI_TARGETS),
            "status": "ready",
            "integrations": links,
            "demo": {"executive": demo["task_id"], "collaborate": collab["ok"], "orchestrate": orch["ok"]},
            "full": {
                "inventory": inv,
                "dashboard": dash,
                "links": links,
                "registry": self.agent_registry(),
                "bus": self.bus_status(),
                "memory": self.memory_read(),
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": list(ARCHITECTURE),
            "principles": self.principles(),
            "version": VERSION,
            "api_prefix": API_PREFIX,
            "path": WEB_PATH,
            "agents": len(self._agents),
        }


multi_agent_os = MultiAgentOSLibrary()
