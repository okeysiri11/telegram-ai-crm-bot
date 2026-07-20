# ConflictResolver — detect and resolve collaboration conflicts.

from __future__ import annotations

from platform_collaboration.models import (
    AgentMessage,
    CollaborationSession,
    CollaborationTask,
    MessageType,
)


class ConflictResolver:
    def detect_conflicts(
        self,
        session: CollaborationSession,
        tasks: list[CollaborationTask],
    ) -> list[dict]:
        conflicts: list[dict] = []

        owners: dict[str, list[str]] = {}
        for task in tasks:
            if task.owner_id:
                owners.setdefault(task.owner_id, []).append(task.task_id)

        for agent_id, task_ids in owners.items():
            if len(task_ids) > 3:
                conflicts.append({
                    "type": "overload",
                    "agent_id": agent_id,
                    "task_count": len(task_ids),
                    "description": f"Agent {agent_id} overloaded with {len(task_ids)} tasks",
                })

        capability_map: dict[str, list[str]] = {}
        for task in tasks:
            if task.capability:
                capability_map.setdefault(task.capability, []).append(task.task_id)
        for cap, tids in capability_map.items():
            capable = [aid for aid, p in session.participants.items() if cap in p.capabilities]
            if len(tids) > len(capable) and capable:
                conflicts.append({
                    "type": "capability_shortage",
                    "capability": cap,
                    "description": f"Not enough agents for capability {cap}",
                })

        failed = [p.agent_id for p in session.participants.values() if p.status == "failed"]
        if failed:
            conflicts.append({
                "type": "agent_failure",
                "agents": failed,
                "description": f"Agent failure: {', '.join(failed)}",
            })

        return conflicts

    def resolve(
        self,
        session: CollaborationSession,
        conflict: dict,
        tasks: list[CollaborationTask],
    ) -> bool:
        ctype = conflict.get("type")

        if ctype == "overload":
            agent_id = conflict["agent_id"]
            agent_tasks = [t for t in tasks if t.owner_id == agent_id and t.status == "pending"]
            idle = [
                aid for aid, p in session.participants.items()
                if p.status == "active" and aid != agent_id
            ]
            for task in agent_tasks[2:]:
                if idle:
                    task.owner_id = idle.pop(0)
                    session.shared_context.assignments[task.task_id] = task.owner_id
            return True

        if ctype == "agent_failure":
            failed_agents = conflict.get("agents", [])
            for task in tasks:
                if task.owner_id in failed_agents and task.status != "completed":
                    replacement = next(
                        (aid for aid, p in session.participants.items() if p.status == "active" and aid not in failed_agents),
                        session.supervisor_id,
                    )
                    if replacement:
                        task.owner_id = replacement
                        task.status = "pending"
            return True

        if ctype == "capability_shortage":
            return True

        return False

    def record_conflict_message(self, session: CollaborationSession, conflict: dict) -> AgentMessage:
        msg = AgentMessage(
            session_id=session.session_id,
            sender_id="system",
            message_type=MessageType.CONFLICT,
            payload=conflict,
        )
        session.messages.append(msg)
        return msg

    def record_resolution_message(self, session: CollaborationSession, conflict: dict) -> AgentMessage:
        msg = AgentMessage(
            session_id=session.session_id,
            sender_id="system",
            message_type=MessageType.NEGOTIATION,
            payload={"resolved": True, **conflict},
        )
        session.messages.append(msg)
        return msg


conflict_resolver = ConflictResolver()
