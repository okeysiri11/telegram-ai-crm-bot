"""Multi-Agent Runtime service façade — Sprint 36.7."""

from __future__ import annotations

from typing import Any

from platform_orchestrator.multi_agent_engine import MultiAgentRuntimeEngine, multi_agent_runtime_engine
from platform_orchestrator.runtime_models import CollaborationMode


class MultiAgentRuntimeService:
    def __init__(self, engine: MultiAgentRuntimeEngine | None = None) -> None:
        self.engine = engine or multi_agent_runtime_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "multi_agent_runtime",
            "canonical": "platform_orchestrator",
            "sprint": "36.7",
            "modes": [m.value for m in CollaborationMode],
            "statistics": self.engine.statistics(),
            "integrations": [
                "ai_runtime",
                "project_memory",
                "context_engine",
                "workflow",
                "event_bus",
                "service_builder",
                "voice_runtime",
            ],
        }

    def register_agent(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.register_agent(body).to_dict()

    def list_agents(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.engine.list_agents(**kwargs)]

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        return self.engine.get_agent(agent_id).to_dict()

    def health(self) -> list[dict[str, Any]]:
        return self.engine.health_all()

    def create_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.create_session(body).to_dict()

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_sessions()]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def update_shared(self, session_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.update_shared(
            session_id,
            context=body.get("shared_context") or body.get("context"),
            memory=body.get("shared_memory") or body.get("memory"),
        ).to_dict()

    async def send_message(self, body: dict[str, Any]) -> dict[str, Any]:
        channel = str(body.get("channel") or "direct")
        if channel == "pubsub":
            msgs = await self.engine.publish(str(body.get("topic") or "default"), body)
            return {"messages": [m.to_dict() for m in msgs], "count": len(msgs)}
        if channel == "event":
            return (await self.engine.emit_event(body)).to_dict()
        return (await self.engine.send_direct(body)).to_dict()

    def subscribe(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.subscribe(str(body.get("agent_id") or ""), str(body.get("topic") or "default"))

    def list_messages(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.engine.list_messages(limit=limit)]

    def plan(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.plan(body).to_dict()

    def list_plans(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.engine.list_plans()]

    def get_plan(self, plan_id: str) -> dict[str, Any]:
        return self.engine.get_plan(plan_id).to_dict()

    def task_graph(self, plan_id: str | None = None) -> dict[str, Any]:
        return self.engine.task_graph(plan_id)

    def enqueue_task(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.enqueue_task(body).to_dict()

    def list_tasks(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.engine.list_tasks()]

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self.engine.get_task(task_id).to_dict()

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        return self.engine.cancel_task(task_id).to_dict()

    def checkpoint_task(self, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.checkpoint_task(task_id, dict(body.get("checkpoint") or body)).to_dict()

    async def run_task(self, task_id: str) -> dict[str, Any]:
        return (await self.engine.run_task(task_id)).to_dict()

    async def orchestrate(self, body: dict[str, Any]) -> dict[str, Any]:
        data = await self.engine.orchestrate(body)
        await self._publish_event("multi_agent.orchestrated", data.get("execution") or {})
        return data

    def list_executions(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.engine.list_executions()]

    def statistics(self) -> dict[str, Any]:
        return self.engine.statistics()

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_ai.service import ai_runtime_service

            ai_runtime_service.ensure_ready()
            completion = await ai_runtime_service.complete(
                {
                    "prompt": str(body.get("goal") or body.get("prompt") or "coordinate agents"),
                    "use_cache": False,
                    "agent_id": "multi_agent",
                }
            )
            ai_out = {"content": (completion.get("content") or "")[:400]}
        except Exception as exc:  # noqa: BLE001
            ai_out = {"error": str(exc)}
        result = await self.orchestrate(
            {
                "goal": body.get("goal") or "AI-assisted collaboration",
                "mode": body.get("mode") or "supervisor_worker",
            }
        )
        return {"consumer": "ai_runtime", "ai": ai_out, **result}

    async def for_project_memory(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        memory = None
        try:
            from platform_memory.project_memory_service import project_memory_service

            memory = await project_memory_service.for_ai_runtime(
                {"query": body.get("goal") or "multi agent", "project_id": body.get("project_id")}
            )
        except Exception as exc:  # noqa: BLE001
            memory = {"error": str(exc)}
        session = self.create_session(
            {
                "goal": body.get("goal") or "memory-backed collaboration",
                "shared_memory": {"project_memory": memory},
                "mode": body.get("mode") or "sequential",
            }
        )
        return {"consumer": "project_memory", "session": session, "memory": memory}

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        ctx = None
        try:
            from platform_memory.service import context_engine_service

            ctx = await context_engine_service.for_ai_runtime(
                {"query": body.get("goal") or "multi agent", "use_project_memory": False}
            )
        except Exception as exc:  # noqa: BLE001
            ctx = {"error": str(exc)}
        session = self.create_session(
            {
                "goal": body.get("goal") or "context-backed collaboration",
                "shared_context": {"enterprise_context": ctx},
            }
        )
        return {"consumer": "context_engine", "session": session, "context": ctx}

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        result = await self.orchestrate(
            {"goal": body.get("goal") or "workflow collaboration", "mode": body.get("mode") or "sequential"}
        )
        try:
            from platform_workflow.service import workflow_runtime_service as wrs

            wrs.ensure_seed()
            run = await wrs.execute(
                "wf_loop_sum",
                {"variables": {"items": [1], "items_out": []}, "actor": "multi_agent"},
            )
            result["workflow"] = {"run_id": run.get("run_id"), "status": run.get("status")}
        except Exception as exc:  # noqa: BLE001
            result["workflow_error"] = str(exc)
        result["consumer"] = "workflow"
        return result

    async def for_service_builder(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_ready()
        from platform_service_builder.service import service_builder

        service_builder.ensure_seed()
        svc = service_builder.get("svc_multi_agent_runtime")
        return {
            "consumer": "service_builder",
            "service_id": svc.id,
            "name": svc.manifest.name,
            "status": self.status(),
            "query": (body or {}).get("query"),
        }

    async def for_voice(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        voice = None
        try:
            from platform_ai.voice_service import voice_runtime_service

            voice = voice_runtime_service.parse(str(body.get("transcript") or "call ai agent to help"))
        except Exception as exc:  # noqa: BLE001
            voice = {"error": str(exc)}
        result = await self.orchestrate(
            {
                "goal": (voice or {}).get("transcript") or body.get("goal") or "voice-driven collaboration",
                "mode": body.get("mode") or "supervisor_worker",
            }
        )
        return {"consumer": "voice_runtime", "voice": voice, **result}

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            from platform_enterprise_event_bus.service import enterprise_event_bus_service as eeb

            await eeb.publish(
                {
                    "topic": "agents",
                    "event_type": event_type,
                    "payload": payload,
                    "source_service": "multi_agent_runtime",
                }
            )
        except Exception:
            pass


multi_agent_runtime_service = MultiAgentRuntimeService()
