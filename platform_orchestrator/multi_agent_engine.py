"""Multi-Agent Runtime engine — Sprint 36.7.

Extends platform_orchestrator: registry enrichment, planner, collaboration modes,
messaging, shared context/memory, task queue with retries/checkpoints/cancel/timeout.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from platform_orchestrator.agents import register_builtin_agents
from platform_orchestrator.message_bus import AgentMessageBus, agent_message_bus
from platform_orchestrator.models import AgentContext, AgentMessage, MessageType, TaskRequest
from platform_orchestrator.orchestrator import PlatformOrchestrator, platform_orchestrator
from platform_orchestrator.runtime_models import (
    AgentCommMessage,
    AgentPlan,
    AgentRecord,
    AgentSession,
    CollaborationMode,
    ExecutionRecord,
    PlanStatus,
    PlanStep,
    RuntimeTask,
    RuntimeTaskStatus,
    new_id,
)


class MultiAgentRuntimeEngine:
    def __init__(
        self,
        *,
        orchestrator: PlatformOrchestrator | None = None,
        message_bus: AgentMessageBus | None = None,
    ) -> None:
        self.orchestrator = orchestrator or platform_orchestrator
        self.bus = message_bus or agent_message_bus
        self.agents: dict[str, AgentRecord] = {}
        self.sessions: dict[str, AgentSession] = {}
        self.plans: dict[str, AgentPlan] = {}
        self.tasks: dict[str, RuntimeTask] = {}
        self.messages: list[AgentCommMessage] = []
        self.executions: dict[str, ExecutionRecord] = {}
        self._pubsub: dict[str, list[str]] = {}  # topic → agent_ids
        self._cancel: set[str] = set()
        self._stats = {
            "orchestrations": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "messages": 0,
            "plans_created": 0,
        }
        self._seeded = False

    def reset(self) -> None:
        self.agents.clear()
        self.sessions.clear()
        self.plans.clear()
        self.tasks.clear()
        self.messages.clear()
        self.executions.clear()
        self._pubsub.clear()
        self._cancel.clear()
        self._stats = {k: 0 for k in self._stats}
        self.orchestrator.reset()
        self.bus.reset()
        self._seeded = False

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        try:
            register_builtin_agents(self.orchestrator.registry)
        except Exception:
            # already registered in this process
            pass
        # Enrich registry records from builtin agents
        for meta in self.orchestrator.registry.list_agents():
            if meta.id in self.agents:
                continue
            self.agents[meta.id] = AgentRecord(
                agent_id=meta.id,
                name=meta.name,
                description=meta.description,
                capabilities=list(meta.capabilities),
                skills=list(meta.capabilities)[:3],
                permissions=["agent.execute", "agent.read"],
                availability="available",
                healthy=True,
                priority=meta.priority,
                version=meta.version,
            )
        # Collaboration specialists
        extras = [
            AgentRecord(
                agent_id="agent_planner",
                name="Planner Agent",
                description="Decomposes goals into executable plans",
                capabilities=["plan", "decompose", "coordinate"],
                skills=["planning", "task_graph"],
                permissions=["agent.execute", "plan.write"],
                priority=120,
            ),
            AgentRecord(
                agent_id="agent_supervisor",
                name="Supervisor Agent",
                description="Supervises workers and aggregates results",
                capabilities=["supervise", "review", "aggregate"],
                skills=["supervision", "qa"],
                permissions=["agent.execute", "agent.supervise"],
                priority=130,
            ),
            AgentRecord(
                agent_id="agent_worker",
                name="Worker Agent",
                description="Generic worker for supervisor-worker mode",
                capabilities=["work", "research", "draft"],
                skills=["execution"],
                permissions=["agent.execute"],
                priority=60,
            ),
        ]
        for rec in extras:
            self.agents.setdefault(rec.agent_id, rec)
        self._seeded = True

    # --- Registry ---

    def register_agent(self, body: dict[str, Any]) -> AgentRecord:
        self.ensure_seed()
        agent_id = str(body.get("agent_id") or new_id("agent"))
        rec = AgentRecord(
            agent_id=agent_id,
            name=str(body.get("name") or agent_id),
            description=str(body.get("description") or ""),
            capabilities=list(body.get("capabilities") or []),
            skills=list(body.get("skills") or []),
            permissions=list(body.get("permissions") or ["agent.execute"]),
            availability=str(body.get("availability") or "available"),
            healthy=bool(body.get("healthy", True)),
            priority=int(body.get("priority") or 50),
            version=str(body.get("version") or "1.0.0"),
            metadata=dict(body.get("metadata") or {}),
        )
        self.agents[agent_id] = rec
        return rec

    def list_agents(self, *, available_only: bool = False) -> list[AgentRecord]:
        self.ensure_seed()
        rows = list(self.agents.values())
        if available_only:
            rows = [a for a in rows if a.availability == "available" and a.healthy]
        return sorted(rows, key=lambda a: a.priority, reverse=True)

    def get_agent(self, agent_id: str) -> AgentRecord:
        self.ensure_seed()
        rec = self.agents.get(agent_id)
        if rec is None:
            raise KeyError(f"agent not found: {agent_id}")
        return rec

    def health_all(self) -> list[dict[str, Any]]:
        self.ensure_seed()
        now = time.time()
        out = []
        for rec in self.agents.values():
            rec.last_health_at = now
            out.append(
                {
                    "agent_id": rec.agent_id,
                    "healthy": rec.healthy,
                    "availability": rec.availability,
                    "status": "ok" if rec.healthy and rec.availability != "offline" else "degraded",
                }
            )
        return out

    # --- Sessions / shared context & memory ---

    def create_session(self, body: dict[str, Any] | None = None) -> AgentSession:
        self.ensure_seed()
        body = body or {}
        mode = str(body.get("mode") or CollaborationMode.SEQUENTIAL.value)
        agent_ids = list(body.get("agent_ids") or [])
        if not agent_ids:
            agent_ids = [a.agent_id for a in self.list_agents(available_only=True)[:3]]
        session = AgentSession(
            session_id=new_id("asess"),
            goal=str(body.get("goal") or body.get("task") or "collaborate"),
            mode=mode,
            agent_ids=agent_ids,
            shared_context=dict(body.get("shared_context") or body.get("context") or {}),
            shared_memory=dict(body.get("shared_memory") or {}),
            metadata=dict(body.get("metadata") or {}),
        )
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> AgentSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"agent session not found: {session_id}")
        return session

    def list_sessions(self) -> list[AgentSession]:
        self.ensure_seed()
        return sorted(self.sessions.values(), key=lambda s: s.created_at, reverse=True)

    def update_shared(self, session_id: str, *, context: dict | None = None, memory: dict | None = None) -> AgentSession:
        session = self.get_session(session_id)
        if context:
            session.shared_context.update(context)
        if memory:
            session.shared_memory.update(memory)
        session.updated_at = time.time()
        return session

    # --- Communication ---

    async def send_direct(self, body: dict[str, Any]) -> AgentCommMessage:
        self.ensure_seed()
        msg = AgentCommMessage(
            message_id=new_id("amsg"),
            channel="direct",
            source_agent_id=str(body.get("source_agent_id") or body.get("from") or "system"),
            target_agent_id=str(body.get("target_agent_id") or body.get("to") or ""),
            payload=dict(body.get("payload") or {}),
        )
        self.messages.append(msg)
        self._stats["messages"] += 1
        await self.bus.publish(
            AgentMessage(
                message_type=MessageType.NOTIFICATION,
                source_agent_id=msg.source_agent_id,
                target_agent_id=msg.target_agent_id,
                payload=msg.payload,
                message_id=msg.message_id,
            )
        )
        return msg

    def subscribe(self, agent_id: str, topic: str) -> dict[str, Any]:
        self.ensure_seed()
        self._pubsub.setdefault(topic, [])
        if agent_id not in self._pubsub[topic]:
            self._pubsub[topic].append(agent_id)
        return {"topic": topic, "subscribers": list(self._pubsub[topic])}

    async def publish(self, topic: str, body: dict[str, Any]) -> list[AgentCommMessage]:
        self.ensure_seed()
        source = str(body.get("source_agent_id") or "system")
        payload = dict(body.get("payload") or body)
        sent: list[AgentCommMessage] = []
        for target in self._pubsub.get(topic, []):
            msg = AgentCommMessage(
                message_id=new_id("amsg"),
                channel="pubsub",
                source_agent_id=source,
                target_agent_id=target,
                topic=topic,
                payload=payload,
            )
            self.messages.append(msg)
            sent.append(msg)
            self._stats["messages"] += 1
        return sent

    async def emit_event(self, body: dict[str, Any]) -> AgentCommMessage:
        msg = AgentCommMessage(
            message_id=new_id("amsg"),
            channel="event",
            source_agent_id=str(body.get("source_agent_id") or "system"),
            topic=str(body.get("event_type") or body.get("topic") or "agent.event"),
            payload=dict(body.get("payload") or {}),
        )
        self.messages.append(msg)
        self._stats["messages"] += 1
        await self.bus.emit_event(msg.source_agent_id, {"event": msg.topic, **msg.payload})
        return msg

    def list_messages(self, *, limit: int = 100) -> list[AgentCommMessage]:
        return list(reversed(self.messages[-limit:]))

    # --- Planner ---

    def plan(self, body: dict[str, Any]) -> AgentPlan:
        self.ensure_seed()
        goal = str(body.get("goal") or body.get("task") or "multi-agent goal")
        mode = CollaborationMode(str(body.get("mode") or CollaborationMode.SEQUENTIAL.value))
        session_id = body.get("session_id")
        available = self.list_agents(available_only=True)
        steps: list[PlanStep] = []

        if mode == CollaborationMode.SEQUENTIAL:
            mapped = []
            for i, a in enumerate(available[:3]):
                cap = a.capabilities[0] if a.capabilities else "work"
                mapped.append((a, cap, f"Step {i+1}: {a.name}"))
            if not mapped:
                mapped = [(available[0] if available else None, "work", "Execute")]
            prev = None
            for a, cap, title in mapped:
                step = PlanStep(
                    step_id=new_id("step"),
                    title=title,
                    capability=cap,
                    agent_id=a.agent_id if a else None,
                    depends_on=[prev] if prev else [],
                    payload={"goal": goal},
                )
                steps.append(step)
                prev = step.step_id

        elif mode == CollaborationMode.PARALLEL:
            for a in available[:4]:
                cap = a.capabilities[0] if a.capabilities else "work"
                steps.append(
                    PlanStep(
                        step_id=new_id("step"),
                        title=f"Parallel: {a.name}",
                        capability=cap,
                        agent_id=a.agent_id,
                        payload={"goal": goal},
                    )
                )

        elif mode == CollaborationMode.HIERARCHICAL:
            supervisor = self.agents.get("agent_supervisor") or (available[0] if available else None)
            workers = [a for a in available if a.agent_id != (supervisor.agent_id if supervisor else "")][:3]
            root = PlanStep(
                step_id=new_id("step"),
                title="Supervise",
                capability="supervise",
                agent_id=supervisor.agent_id if supervisor else None,
                payload={"goal": goal, "role": "supervisor"},
            )
            steps.append(root)
            for w in workers:
                steps.append(
                    PlanStep(
                        step_id=new_id("step"),
                        title=f"Worker: {w.name}",
                        capability=w.capabilities[0] if w.capabilities else "work",
                        agent_id=w.agent_id,
                        depends_on=[root.step_id],
                        payload={"goal": goal, "role": "worker"},
                    )
                )

        elif mode == CollaborationMode.SWARM:
            for a in available[:5]:
                steps.append(
                    PlanStep(
                        step_id=new_id("step"),
                        title=f"Swarm: {a.name}",
                        capability=a.capabilities[0] if a.capabilities else "work",
                        agent_id=a.agent_id,
                        payload={"goal": goal, "swarm": True},
                    )
                )

        else:  # SUPERVISOR_WORKER
            supervisor = self.agents.get("agent_supervisor")
            worker = self.agents.get("agent_worker") or (available[0] if available else None)
            s = PlanStep(
                step_id=new_id("step"),
                title="Assign work",
                capability="supervise",
                agent_id=supervisor.agent_id if supervisor else None,
                payload={"goal": goal},
            )
            w = PlanStep(
                step_id=new_id("step"),
                title="Execute work",
                capability=worker.capabilities[0] if worker and worker.capabilities else "work",
                agent_id=worker.agent_id if worker else None,
                depends_on=[s.step_id],
                payload={"goal": goal},
            )
            steps = [s, w]

        plan = AgentPlan(
            plan_id=new_id("plan"),
            session_id=session_id,
            goal=goal,
            mode=mode,
            steps=steps,
            status=PlanStatus.READY,
        )
        self.plans[plan.plan_id] = plan
        self._stats["plans_created"] += 1
        return plan

    def list_plans(self) -> list[AgentPlan]:
        self.ensure_seed()
        return sorted(self.plans.values(), key=lambda p: p.created_at, reverse=True)

    def get_plan(self, plan_id: str) -> AgentPlan:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise KeyError(f"plan not found: {plan_id}")
        return plan

    def task_graph(self, plan_id: str | None = None) -> dict[str, Any]:
        self.ensure_seed()
        plans = [self.get_plan(plan_id)] if plan_id else self.list_plans()[:5]
        nodes = []
        edges = []
        for plan in plans:
            for step in plan.steps:
                nodes.append(
                    {
                        "id": step.step_id,
                        "label": step.title,
                        "agent_id": step.agent_id,
                        "status": step.status,
                        "plan_id": plan.plan_id,
                    }
                )
                for dep in step.depends_on:
                    edges.append({"from": dep, "to": step.step_id, "plan_id": plan.plan_id})
        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    # --- Task runtime ---

    def enqueue_task(self, body: dict[str, Any]) -> RuntimeTask:
        self.ensure_seed()
        task = RuntimeTask(
            task_id=new_id("atask"),
            title=str(body.get("title") or body.get("goal") or "task"),
            capability=str(body.get("capability") or "work"),
            agent_id=body.get("agent_id"),
            session_id=body.get("session_id"),
            plan_id=body.get("plan_id"),
            payload=dict(body.get("payload") or {}),
            max_retries=int(body.get("max_retries") or 2),
            timeout_sec=float(body.get("timeout_sec") or 30),
            schedule_at=body.get("schedule_at"),
            status=RuntimeTaskStatus.SCHEDULED if body.get("schedule_at") else RuntimeTaskStatus.QUEUED,
        )
        self.tasks[task.task_id] = task
        return task

    def list_tasks(self, *, limit: int = 100) -> list[RuntimeTask]:
        rows = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
        return rows[:limit]

    def get_task(self, task_id: str) -> RuntimeTask:
        task = self.tasks.get(task_id)
        if task is None:
            raise KeyError(f"task not found: {task_id}")
        return task

    def cancel_task(self, task_id: str) -> RuntimeTask:
        task = self.get_task(task_id)
        self._cancel.add(task_id)
        task.status = RuntimeTaskStatus.CANCELLED
        task.updated_at = time.time()
        self._stats["tasks_cancelled"] += 1
        return task

    def checkpoint_task(self, task_id: str, checkpoint: dict[str, Any]) -> RuntimeTask:
        task = self.get_task(task_id)
        task.checkpoint.update(checkpoint)
        task.status = RuntimeTaskStatus.CHECKPOINTED
        task.updated_at = time.time()
        return task

    async def _run_single_capability(
        self,
        *,
        capability: str,
        payload: dict[str, Any],
        agent_id: str | None,
        timeout_sec: float,
        max_retries: int,
        context: AgentContext,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        # Prefer platform orchestrator when capability exists on builtin agents
        try:
            orch_task = TaskRequest(
                capability=capability,
                payload=payload,
                context=context,
                task_id=task_id or new_id("otask"),
                timeout_seconds=timeout_sec,
                max_retries=max_retries,
            )
            # If capability unknown to router, fall through to simulated worker
            caps = self.orchestrator.registry.capabilities()
            if capability in caps:
                result = await self.orchestrator.execute_async(orch_task)
                return {
                    "agent_id": result.agent_id,
                    "capability": capability,
                    "status": result.status.value,
                    "output": result.output,
                    "error": result.error,
                    "retries": result.retries,
                }
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
        else:
            last = "capability not in orchestrator registry"

        # Simulated specialist / worker execution
        await asyncio.sleep(0)  # yield
        chosen = agent_id or (self.list_agents(available_only=True)[0].agent_id if self.agents else "agent_worker")
        return {
            "agent_id": chosen,
            "capability": capability,
            "status": "completed",
            "output": {"acknowledged": True, "payload": payload, "note": last},
            "error": None,
            "retries": 0,
        }

    async def run_task(self, task_id: str) -> RuntimeTask:
        task = self.get_task(task_id)
        if task.task_id in self._cancel:
            task.status = RuntimeTaskStatus.CANCELLED
            return task
        if task.schedule_at and task.schedule_at > time.time():
            task.status = RuntimeTaskStatus.SCHEDULED
            return task

        task.status = RuntimeTaskStatus.RUNNING
        task.updated_at = time.time()
        session = self.sessions.get(task.session_id) if task.session_id else None
        shared_context = session.shared_context if session else {}
        context = AgentContext(
            platform_context={"multi_agent": True},
            memory_context=dict(session.shared_memory) if session else {},
            session_context=dict(shared_context),
            permissions=["agent.execute"],
            # Sprint 47.0 — best-effort passthrough: populated only when the session
            # creator actually supplied these (see create_session's shared_context);
            # nothing upstream fabricates a tenant/vertical/customer/user here.
            tenant_id=shared_context.get("tenant_id"),
            vertical=shared_context.get("vertical"),
            customer_id=shared_context.get("customer_id"),
            user_id=shared_context.get("user_id"),
        )

        try:
            while True:
                if task.task_id in self._cancel:
                    task.status = RuntimeTaskStatus.CANCELLED
                    self._stats["tasks_cancelled"] += 1
                    break
                try:
                    out = await asyncio.wait_for(
                        self._run_single_capability(
                            capability=task.capability,
                            payload=task.payload,
                            agent_id=task.agent_id,
                            timeout_sec=task.timeout_sec,
                            max_retries=0,
                            context=context,
                            task_id=task.task_id,
                        ),
                        timeout=task.timeout_sec,
                    )
                    task.result = out
                    task.agent_id = out.get("agent_id") or task.agent_id
                    task.checkpoint = {"last": out}
                    if out.get("status") in ("completed", "COMPLETED") or out.get("output"):
                        task.status = RuntimeTaskStatus.COMPLETED
                        self._stats["tasks_completed"] += 1
                        break
                    raise RuntimeError(out.get("error") or "task failed")
                except asyncio.TimeoutError:
                    task.retries += 1
                    task.status = RuntimeTaskStatus.RETRYING
                    if task.retries > task.max_retries:
                        task.status = RuntimeTaskStatus.TIMEOUT
                        task.error = "timeout"
                        self._stats["tasks_failed"] += 1
                        break
                except Exception as exc:  # noqa: BLE001
                    task.retries += 1
                    task.error = str(exc)
                    task.status = RuntimeTaskStatus.RETRYING
                    if task.retries > task.max_retries:
                        task.status = RuntimeTaskStatus.FAILED
                        self._stats["tasks_failed"] += 1
                        break
        finally:
            task.updated_at = time.time()
        return task

    # --- Orchestrate collaboration ---

    async def orchestrate(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_seed()
        session = None
        if body.get("session_id"):
            session = self.get_session(str(body["session_id"]))
        else:
            session = self.create_session(body)

        mode = CollaborationMode(str(body.get("mode") or session.mode.value))
        session.mode = mode
        plan = self.plan(
            {
                "goal": body.get("goal") or session.goal,
                "mode": mode.value,
                "session_id": session.session_id,
            }
        )
        plan.status = PlanStatus.RUNNING

        execution = ExecutionRecord(
            execution_id=new_id("aexec"),
            session_id=session.session_id,
            plan_id=plan.plan_id,
            mode=mode.value,
            status="running",
        )
        self.executions[execution.execution_id] = execution
        self._stats["orchestrations"] += 1

        results: list[dict[str, Any]] = []

        async def _exec_step(step: PlanStep) -> dict[str, Any]:
            if any(self.plans[plan.plan_id].steps and False for _ in []):
                pass
            # dependency gate
            for dep in step.depends_on:
                dep_step = next((s for s in plan.steps if s.step_id == dep), None)
                if dep_step and dep_step.status != "completed":
                    return {"step_id": step.step_id, "status": "blocked", "depends_on": dep}

            rt = self.enqueue_task(
                {
                    "title": step.title,
                    "capability": step.capability,
                    "agent_id": step.agent_id,
                    "session_id": session.session_id,
                    "plan_id": plan.plan_id,
                    "payload": {**step.payload, "shared_context": session.shared_context},
                    "timeout_sec": float(body.get("timeout_sec") or 15),
                    "max_retries": int(body.get("max_retries") or 1),
                }
            )
            step.status = "running"
            done = await self.run_task(rt.task_id)
            step.status = "completed" if done.status == RuntimeTaskStatus.COMPLETED else done.status.value
            step.result = done.result
            step.agent_id = done.agent_id or step.agent_id
            # shared memory update
            session.shared_memory[step.step_id] = done.result
            session.updated_at = time.time()
            await self.emit_event(
                {
                    "source_agent_id": step.agent_id or "orchestrator",
                    "event_type": "agent.step.completed",
                    "payload": {"step_id": step.step_id, "status": step.status},
                }
            )
            return {"step_id": step.step_id, "task": done.to_dict(), "status": step.status}

        if mode in (CollaborationMode.PARALLEL, CollaborationMode.SWARM):
            results = list(await asyncio.gather(*[_exec_step(s) for s in plan.steps]))
        elif mode == CollaborationMode.HIERARCHICAL:
            # supervisor first, then workers in parallel
            roots = [s for s in plan.steps if not s.depends_on]
            children = [s for s in plan.steps if s.depends_on]
            for r in roots:
                results.append(await _exec_step(r))
            if children:
                results.extend(await asyncio.gather(*[_exec_step(s) for s in children]))
        else:
            # sequential / supervisor_worker — honor depends_on order
            remaining = list(plan.steps)
            completed_ids: set[str] = set()
            safety = 0
            while remaining and safety < 50:
                safety += 1
                progress = False
                for step in list(remaining):
                    if all(d in completed_ids for d in step.depends_on):
                        results.append(await _exec_step(step))
                        completed_ids.add(step.step_id)
                        remaining.remove(step)
                        progress = True
                if not progress:
                    break

        aggregated = self._aggregate(results, mode=mode, goal=plan.goal)
        plan.status = PlanStatus.COMPLETED
        plan.updated_at = time.time()
        execution.results = results
        execution.aggregated = aggregated
        execution.status = "completed"
        execution.finished_at = time.time()
        session.status = "completed"
        session.updated_at = time.time()

        return {
            "execution": execution.to_dict(),
            "session": session.to_dict(),
            "plan": plan.to_dict(),
            "aggregated": aggregated,
            "task_graph": self.task_graph(plan.plan_id),
        }

    def _aggregate(self, results: list[dict[str, Any]], *, mode: CollaborationMode, goal: str) -> dict[str, Any]:
        ok = sum(1 for r in results if r.get("status") == "completed")
        return {
            "goal": goal,
            "mode": mode.value,
            "steps_total": len(results),
            "steps_completed": ok,
            "success_rate": (ok / len(results)) if results else 0.0,
            "outputs": [r.get("task", {}).get("result") for r in results],
            "supervisor": "agent_supervisor" if mode in (CollaborationMode.HIERARCHICAL, CollaborationMode.SUPERVISOR_WORKER) else None,
        }

    def list_executions(self, *, limit: int = 50) -> list[ExecutionRecord]:
        rows = sorted(self.executions.values(), key=lambda e: e.created_at, reverse=True)
        return rows[:limit]

    def statistics(self) -> dict[str, Any]:
        self.ensure_seed()
        return {
            **self._stats,
            "agents": len(self.agents),
            "sessions": len(self.sessions),
            "plans": len(self.plans),
            "tasks": len(self.tasks),
            "messages": len(self.messages),
            "executions": len(self.executions),
            "modes": [m.value for m in CollaborationMode],
        }


multi_agent_runtime_engine = MultiAgentRuntimeEngine()
