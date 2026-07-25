"""Collaborative AI Engine — Sprint 28.8 Enterprise Collective Intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.collaborative_ai.catalogs import (
    CONSENSUS_STATES,
    DEFAULT_CONCIERGE,
    DEFAULT_SPECIALISTS,
    OPS_FOUNDATION_SURFACES,
    PERFORMANCE_METRICS,
    PRIORITIES,
    ROLE_TEMPLATES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.group_ai import GROUP_AI_CHAT_FOUNDATION
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _visual_id(object_type: str, internal_id: str) -> str:
    return f"viz_{object_type}_{internal_id}"


class CollaborativeAIEngine:
    """Multiple AI Specialists coordinated by Concierge as one organization."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "28.8",
            "collaborative_ai_ready": True,
            "collective_intelligence_ready": True,
            "decision_engine_ready": True,
            "knowledge_exchange_ready": True,
            "ai_team_ready": True,
            "ai_ops_foundation_ready": True,
            "group_ai_foundation": {
                **GROUP_AI_CHAT_FOUNDATION,
                "status": "operational",
                "note": "Collaborative AI Engine runtime — Sprint 28.8",
            },
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "28.8",
            "teams": len(self.store.collaborative_teams.list_all()),
            "sessions": len(self.store.collaborative_sessions.list_all()),
            "decisions": len(self.store.collaborative_decisions.list_all()),
            "knowledge_exchanges": len(self.store.collaborative_knowledge.list_all()),
            "wizard_steps": len(WIZARD_STEPS),
        }

    # --- Step 1: AI Team Creation ---

    def create_team(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload or {}
        name = (data.get("team_name") or data.get("name") or "Enterprise AI Team").strip()
        specialists = data.get("specialists") or [dict(s) for s in DEFAULT_SPECIALISTS[:3]]
        concierge = data.get("concierge") or dict(DEFAULT_CONCIERGE)
        priority = (data.get("priority") or "high").lower()
        if priority not in PRIORITIES:
            raise ValidationError(f"priority must be one of {PRIORITIES}")
        tid = _id("aitm")
        record = {
            "team_id": tid,
            "internal_id": tid,
            "visual_id": _visual_id("ai_team", tid),
            "object_type": "ai_team",
            "team_name": name,
            "business_goal": data.get("business_goal") or "Coordinate specialists for a unified decision",
            "priority": priority,
            "specialists": specialists,
            "concierge": concierge,
            "roles": [],
            "status": "formed",
            "lifecycle": "registered",
            "logical_state": {
                "phase": "created",
                "participant_count": len(specialists) + 1,
                "visualization_ready": True,
            },
            "created_at": _now(),
            "updated_at": _now(),
            "sprint": "28.8",
        }
        self.store.collaborative_teams.save(tid, record)
        return record

    def get_team(self, team_id: str) -> dict[str, Any]:
        team = self.store.collaborative_teams.get(team_id)
        if not team:
            raise NotFoundError(f"AI Team not found: {team_id}")
        return team

    def list_teams(self) -> dict[str, Any]:
        items = self.store.collaborative_teams.list_all()
        return {"count": len(items), "teams": items}

    # --- Step 2: Role Assignment ---

    def assign_roles(self, team_id: str, assignments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        team = self.get_team(team_id)
        roles: list[dict[str, Any]] = []
        specialists = team["specialists"]
        templates = list(ROLE_TEMPLATES)
        for i, spec in enumerate(specialists):
            template = templates[min(i, len(templates) - 2)]
            custom = (assignments or [])[i] if assignments and i < len(assignments) else {}
            roles.append(
                {
                    "specialist_id": spec.get("id") or f"spec_{i}",
                    "specialist_name": spec.get("name") or f"Specialist {i + 1}",
                    "role": custom.get("role") or template["role"],
                    "responsibilities": custom.get("responsibilities") or list(template["responsibilities"]),
                    "priority": custom.get("priority") or template["priority"],
                    "permissions": custom.get("permissions") or list(template["permissions"]),
                    "knowledge_scope": custom.get("knowledge_scope") or list(template["knowledge_scope"]),
                    "expected_output": custom.get("expected_output") or template["expected_output"],
                }
            )
        # Concierge always Orchestrator
        roles.append(
            {
                "specialist_id": team["concierge"].get("id") or "concierge_org",
                "specialist_name": team["concierge"].get("name") or "Concierge",
                "role": "Orchestrator",
                "responsibilities": list(ROLE_TEMPLATES[-1]["responsibilities"]),
                "priority": "critical",
                "permissions": list(ROLE_TEMPLATES[-1]["permissions"]),
                "knowledge_scope": list(ROLE_TEMPLATES[-1]["knowledge_scope"]),
                "expected_output": ROLE_TEMPLATES[-1]["expected_output"],
            }
        )
        team["roles"] = roles
        team["updated_at"] = _now()
        team["logical_state"]["phase"] = "roles_assigned"
        self.store.collaborative_teams.save(team_id, team)
        return {"team_id": team_id, "roles": roles, "count": len(roles)}

    # --- Step 3: Collaborative Session ---

    def start_collab_session(self, team_id: str, topic: str | None = None) -> dict[str, Any]:
        team = self.get_team(team_id)
        if not team.get("roles"):
            self.assign_roles(team_id)
            team = self.get_team(team_id)
        sid = _id("cais")
        concierge_id = team["concierge"].get("id") or "concierge_org"
        record = {
            "session_id": sid,
            "internal_id": sid,
            "visual_id": _visual_id("collab_session", sid),
            "object_type": "collaborative_session",
            "team_id": team_id,
            "topic": topic or team["business_goal"],
            "participants": [
                {
                    "id": r["specialist_id"],
                    "name": r["specialist_name"],
                    "role": r["role"],
                    "visual_id": _visual_id("participant", r["specialist_id"]),
                }
                for r in team["roles"]
            ],
            "current_speaker": concierge_id,
            "current_task": "Open collaborative workspace and frame the goal",
            "discussion_progress": 0.1,
            "consensus_status": "forming",
            "tasks": [],
            "knowledge_board": [],
            "status": "active",
            "lifecycle": "in_progress",
            "logical_state": {
                "phase": "session_open",
                "speaker": concierge_id,
                "consensus": "forming",
                "visualization_ready": True,
            },
            "created_at": _now(),
            "updated_at": _now(),
            "sprint": "28.8",
        }
        self.store.collaborative_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.collaborative_sessions.get(session_id)
        if not session:
            # wizard sessions live in collab_wizard_sessions
            wizard = self.store.collab_wizard_sessions.get(session_id)
            if wizard:
                return wizard
            raise NotFoundError(f"Collaborative session not found: {session_id}")
        return session

    def session_workspace(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "participants" not in session:
            raise ValidationError("Not a collaborative workspace session")
        return {
            "session_id": session_id,
            "participants": session["participants"],
            "current_speaker": session["current_speaker"],
            "current_task": session["current_task"],
            "discussion_progress": session["discussion_progress"],
            "consensus_status": session["consensus_status"],
            "consensus_states": list(CONSENSUS_STATES),
            "visual_id": session["visual_id"],
            "logical_state": session["logical_state"],
        }

    # --- Step 4: Task Distribution ---

    def distribute_tasks(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        team = self.get_team(session["team_id"])
        tasks = []
        specialists = [r for r in team["roles"] if r["role"] != "Orchestrator"]
        for i, role in enumerate(specialists):
            tid = _id("ctask")
            task = {
                "task_id": tid,
                "internal_id": tid,
                "visual_id": _visual_id("task", tid),
                "assigned_to": role["specialist_id"],
                "assignee_name": role["specialist_name"],
                "role": role["role"],
                "title": f"{role['expected_output']} for «{session['topic']}»",
                "status": "assigned",
                "priority": role["priority"],
                "workload_weight": round(1.0 / max(len(specialists), 1), 2),
                "result": None,
            }
            tasks.append(task)
        # Concierge coordinates
        coord_id = _id("ctask")
        tasks.append(
            {
                "task_id": coord_id,
                "internal_id": coord_id,
                "visual_id": _visual_id("task", coord_id),
                "assigned_to": team["concierge"].get("id") or "concierge_org",
                "assignee_name": team["concierge"].get("name") or "Concierge",
                "role": "Orchestrator",
                "title": "Coordinate specialists and collect results",
                "status": "in_progress",
                "priority": "critical",
                "workload_weight": 0.25,
                "result": None,
            }
        )
        # Simulate collection
        for task in tasks:
            if task["role"] != "Orchestrator":
                task["status"] = "completed"
                task["result"] = {
                    "summary": f"{task['assignee_name']} completed «{task['title']}»",
                    "confidence": 0.82,
                    "findings": [f"Finding from {task['role']}"],
                }
            else:
                task["status"] = "completed"
                task["result"] = {
                    "summary": "Concierge collected and balanced specialist outputs",
                    "collected": [t["task_id"] for t in tasks if t["role"] != "Orchestrator"],
                }
        session["tasks"] = tasks
        session["current_task"] = "Collect and synthesize specialist results"
        session["current_speaker"] = team["concierge"].get("id") or "concierge_org"
        session["discussion_progress"] = 0.55
        session["consensus_status"] = "debating"
        session["logical_state"].update({"phase": "tasks_distributed", "consensus": "debating"})
        session["updated_at"] = _now()
        self.store.collaborative_sessions.save(session_id, session)
        return {
            "session_id": session_id,
            "tasks": tasks,
            "assigned": len(tasks),
            "completed": sum(1 for t in tasks if t["status"] == "completed"),
            "balanced": True,
            "coordinator": "concierge",
        }

    # --- Step 5: Shared Knowledge ---

    def share_knowledge(self, session_id: str, entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        board = list(session.get("knowledge_board") or [])
        if entries:
            for e in entries:
                kid = _id("cknow")
                board.append(
                    {
                        "exchange_id": kid,
                        "internal_id": kid,
                        "visual_id": _visual_id("knowledge", kid),
                        "from": e.get("from") or "specialist",
                        "context": e.get("context") or "",
                        "reference": e.get("reference") or "",
                        "finding": e.get("finding") or "",
                        "shared_at": _now(),
                    }
                )
        else:
            for task in session.get("tasks") or []:
                if task.get("result") and task["role"] != "Orchestrator":
                    kid = _id("cknow")
                    board.append(
                        {
                            "exchange_id": kid,
                            "internal_id": kid,
                            "visual_id": _visual_id("knowledge", kid),
                            "from": task["assignee_name"],
                            "context": session["topic"],
                            "reference": f"task:{task['task_id']}",
                            "finding": (task["result"].get("findings") or ["Shared finding"])[0],
                            "shared_at": _now(),
                        }
                    )
        conclusions = [
            {
                "conclusion_id": _id("cconc"),
                "text": "Shared board supports a coordinated recommendation",
                "supported_by": [b["exchange_id"] for b in board[:3]],
            }
        ]
        session["knowledge_board"] = board
        session["shared_conclusions"] = conclusions
        session["discussion_progress"] = 0.7
        session["consensus_status"] = "converging"
        session["logical_state"].update({"phase": "knowledge_shared", "consensus": "converging"})
        session["updated_at"] = _now()
        self.store.collaborative_sessions.save(session_id, session)

        exchange = {
            "exchange_pack_id": _id("ckx"),
            "session_id": session_id,
            "entries": board,
            "conclusions": conclusions,
            "created_at": _now(),
        }
        self.store.collaborative_knowledge.save(exchange["exchange_pack_id"], exchange)
        return exchange

    # --- Step 6: Decision Engine ---

    def decide(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        topic = session.get("topic") or "business goal"
        alternatives = [
            {
                "id": "alt_a",
                "title": f"Proceed with coordinated plan for «{topic}»",
                "pros": ["Unified specialist input", "Concierge orchestration", "Audit-ready trail"],
                "cons": ["Requires follow-up ownership", "Slightly longer cycle"],
                "risk_notes": ["Dependency on specialist availability"],
            },
            {
                "id": "alt_b",
                "title": "Defer decision pending more data",
                "pros": ["Lower immediate risk", "More time for research"],
                "cons": ["Delayed value", "Momentum loss"],
                "risk_notes": ["Opportunity cost"],
            },
            {
                "id": "alt_c",
                "title": "Pilot with a subset of specialists",
                "pros": ["Faster validation", "Controlled scope"],
                "cons": ["Incomplete coverage", "May miss cross-domain risks"],
                "risk_notes": ["Pilot bias"],
            },
        ]
        recommended = alternatives[0]
        decision = {
            "decision_id": _id("cdec"),
            "internal_id": None,
            "visual_id": None,
            "session_id": session_id,
            "team_id": session["team_id"],
            "alternatives": alternatives,
            "recommended_decision": recommended["title"],
            "recommended_id": recommended["id"],
            "business_impact": "Accelerates coordinated execution with clear accountability across the AI organization.",
            "pros": recommended["pros"],
            "cons": recommended["cons"],
            "risk_notes": recommended["risk_notes"],
            "created_at": _now(),
            "object_type": "decision",
            "logical_state": {"phase": "decided", "visualization_ready": True},
        }
        decision["internal_id"] = decision["decision_id"]
        decision["visual_id"] = _visual_id("decision", decision["decision_id"])
        self.store.collaborative_decisions.save(decision["decision_id"], decision)
        session["decision_id"] = decision["decision_id"]
        session["discussion_progress"] = 0.85
        session["consensus_status"] = "reached"
        session["logical_state"].update({"phase": "decision_ready", "consensus": "reached"})
        session["updated_at"] = _now()
        self.store.collaborative_sessions.save(session_id, session)
        return decision

    # --- Step 7: Executive Summary ---

    def executive_summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        decision_id = session.get("decision_id")
        decision = self.store.collaborative_decisions.get(decision_id) if decision_id else None
        if not decision:
            decision = self.decide(session_id)
        report = {
            "report_id": _id("crep"),
            "session_id": session_id,
            "final_report": f"Collaborative session on «{session['topic']}» reached consensus via Concierge orchestration.",
            "executive_summary": (
                f"The AI Team recommends: {decision['recommended_decision']}. "
                "Specialists contributed domain findings; Concierge unified the answer."
            ),
            "decision_explanation": (
                "Chosen because it maximizes coordinated specialist coverage while keeping "
                "an auditable orchestration trail for the organization."
            ),
            "action_plan": [
                "Publish unified answer to stakeholders",
                "Assign owners for each mitigation",
                "Schedule follow-up collaborative review",
                "Register decision in team knowledge",
            ],
            "decision": decision,
            "created_at": _now(),
        }
        session["executive_report"] = report
        session["discussion_progress"] = 0.95
        session["updated_at"] = _now()
        self.store.collaborative_sessions.save(session_id, session)
        return report

    # --- Step 8: Team Performance ---

    def performance(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        tasks = session.get("tasks") or []
        completed = [t for t in tasks if t.get("status") == "completed"]
        contributions = []
        for t in tasks:
            if t["role"] == "Orchestrator":
                continue
            contributions.append(
                {
                    "specialist": t["assignee_name"],
                    "role": t["role"],
                    "tasks_completed": 1 if t["status"] == "completed" else 0,
                    "contribution_score": 0.78,
                    "knowledge_items": sum(
                        1
                        for k in (session.get("knowledge_board") or [])
                        if k.get("from") == t["assignee_name"]
                    ),
                }
            )
        return {
            "session_id": session_id,
            "metrics": {
                "Completed Tasks": len(completed),
                "Average Response Time": "1.2s (simulated)",
                "Collaboration Quality": 0.86,
                "Knowledge Usage": len(session.get("knowledge_board") or []),
                "Specialist Contribution": contributions,
            },
            "metric_names": list(PERFORMANCE_METRICS),
            "ready": True,
        }

    # --- Step 9: Explain Decision ---

    def explain_decision(self, session_id: str, recommendation: str | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        decision = None
        if session.get("decision_id"):
            decision = self.store.collaborative_decisions.get(session["decision_id"])
        text = recommendation or (decision or {}).get("recommended_decision") or "Coordinated plan"
        return {
            "recommendation": text,
            "why_this_recommendation": (
                f"«{text}» was selected because Concierge-balanced specialist outputs "
                "converged with acceptable risk."
            ),
            "business_benefits": [
                "Faster cross-domain decisions",
                "Clear ownership via Concierge orchestration",
                "Reusable knowledge exchange trail",
            ],
            "alternative_approaches": [
                a["title"] for a in ((decision or {}).get("alternatives") or []) if a["title"] != text
            ]
            or ["Defer for more data", "Run a limited pilot"],
            "expected_result": "Unified organizational answer with traceable specialist contributions",
        }

    # --- Step 10: AI Ops Center Foundation ---

    def ops_foundation(self, team_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
        objects = []
        if team_id:
            team = self.get_team(team_id)
            objects.append(
                {
                    "internal_id": team["internal_id"],
                    "visual_id": team["visual_id"],
                    "object_type": team["object_type"],
                    "logical_state": team["logical_state"],
                    "label": team["team_name"],
                }
            )
        if session_id:
            session = self.get_session(session_id)
            objects.append(
                {
                    "internal_id": session["internal_id"],
                    "visual_id": session["visual_id"],
                    "object_type": session["object_type"],
                    "logical_state": session["logical_state"],
                    "label": session.get("topic"),
                }
            )
            for p in session.get("participants") or []:
                objects.append(
                    {
                        "internal_id": p["id"],
                        "visual_id": p["visual_id"],
                        "object_type": "ai_participant",
                        "logical_state": {"role": p["role"], "visualization_ready": True},
                        "label": p["name"],
                    }
                )
        return {
            "title": "Foundation for AI Operations Center",
            "surfaces": list(OPS_FOUNDATION_SURFACES),
            "ai_team_map": objects,
            "visual_layer_ready": True,
            "visual_ids_ready": True,
            "live_organization_ready": True,
            "ai_city_2d_integration_ready": True,
            "objects": objects,
            "note": "Logical state exposed for future Visual Layer and 2D AI City.",
        }

    # --- Wizard session (steps 1–11 studio) ---

    def start_wizard(self, owner_id: str | None = None) -> dict[str, Any]:
        wid = _id("cwiz")
        record = {
            "session_id": wid,
            "wizard": True,
            "status": "in_progress",
            "step": 1,
            "owner_id": owner_id or "platform_owner",
            "draft": {
                "team_name": "Enterprise Collective Team",
                "business_goal": "Deliver a unified cross-domain recommendation",
                "priority": "high",
                "specialist_ids": [s["id"] for s in DEFAULT_SPECIALISTS[:3]],
                "concierge_id": DEFAULT_CONCIERGE["id"],
                "topic": None,
                "team_id": None,
                "collab_session_id": None,
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.collab_wizard_sessions.save(wid, record)
        return record

    def get_wizard(self, session_id: str) -> dict[str, Any]:
        session = self.store.collab_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Collaborative wizard session not found: {session_id}")
        return session

    def update_wizard(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_wizard(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 11:
                raise ValidationError("step must be between 1 and 11")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        session["updated_at"] = _now()
        self.store.collab_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        wizard = self.get_wizard(session_id)
        draft = wizard["draft"]
        team_id = draft.get("team_id")
        collab_id = draft.get("collab_session_id")
        payload: dict[str, Any] = {
            "session_id": session_id,
            "title": "Collaborative AI Summary",
            "draft": draft,
        }
        if team_id:
            payload["team"] = self.get_team(team_id)
            payload["ops_foundation"] = self.ops_foundation(team_id=team_id, session_id=collab_id)
        if collab_id:
            payload["workspace"] = self.session_workspace(collab_id)
            payload["performance"] = self.performance(collab_id)
            if self.get_session(collab_id).get("decision_id"):
                payload["explain"] = self.explain_decision(collab_id)
        return payload

    def create(self, session_id: str) -> dict[str, Any]:
        wizard = self.get_wizard(session_id)
        draft = wizard["draft"]

        specialists = [
            next((dict(s) for s in DEFAULT_SPECIALISTS if s["id"] == sid), {"id": sid, "name": sid})
            for sid in (draft.get("specialist_ids") or [s["id"] for s in DEFAULT_SPECIALISTS[:3]])
        ]
        team = self.create_team(
            {
                "team_name": draft.get("team_name"),
                "business_goal": draft.get("business_goal"),
                "priority": draft.get("priority") or "high",
                "specialists": specialists,
                "concierge": dict(DEFAULT_CONCIERGE)
                if draft.get("concierge_id") == DEFAULT_CONCIERGE["id"]
                else {"id": draft.get("concierge_id"), "name": "Concierge"},
            }
        )
        self.assign_roles(team["team_id"])
        collab = self.start_collab_session(team["team_id"], topic=draft.get("topic") or draft.get("business_goal"))
        tasks = self.distribute_tasks(collab["session_id"])
        knowledge = self.share_knowledge(collab["session_id"])
        decision = self.decide(collab["session_id"])
        report = self.executive_summary(collab["session_id"])
        performance = self.performance(collab["session_id"])
        explain = self.explain_decision(collab["session_id"])
        ops = self.ops_foundation(team_id=team["team_id"], session_id=collab["session_id"])

        wizard["status"] = "created"
        wizard["draft"]["team_id"] = team["team_id"]
        wizard["draft"]["collab_session_id"] = collab["session_id"]
        wizard["updated_at"] = _now()
        self.store.collab_wizard_sessions.save(session_id, wizard)

        return {
            "ok": True,
            "session_id": session_id,
            "ai_team": team,
            "collaborative_session": collab,
            "decision_engine": decision,
            "knowledge_exchange": knowledge,
            "task_distribution": tasks,
            "executive_summary": report,
            "performance": performance,
            "explain": explain,
            "ops_foundation": ops,
            "message": "AI Team, Collaborative Session, Decision Engine, and Knowledge Exchange registered.",
        }
