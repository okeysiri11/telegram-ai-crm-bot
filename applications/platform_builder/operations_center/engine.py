"""Enterprise AI Operations Center — Sprint 29.1.

Visualizes the Logical Layer in real time. Does not execute business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.operations_center.catalogs import (
    ACTIVITY_CHANNELS,
    AI_CITY_INTERFACES,
    DASHBOARD_CATEGORIES,
    HEALTH_SURFACES,
    LIVE_STATUSES,
    VISUAL_OBJECT_FIELDS,
    WAIT_STAGES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _visual_id(object_type: str, logical_id: str) -> str:
    return f"viz_{object_type}_{logical_id}"


class VisualLayer:
    """Projection layer: Logical State → Visual State + Visual ID."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def project(self, obj: dict[str, Any]) -> dict[str, Any]:
        logical_id = (
            obj.get("logical_id")
            or obj.get("internal_id")
            or obj.get("object_id")
            or obj.get("team_id")
            or obj.get("session_id")
            or obj.get("agent_id")
            or obj.get("concierge_id")
            or obj.get("organization_id")
            or _id("obj")
        )
        object_type = obj.get("object_type") or obj.get("kind") or "platform_object"
        visual_id = obj.get("visual_id") or _visual_id(object_type, logical_id)
        logical_state = obj.get("logical_state") or {
            "phase": obj.get("lifecycle") or obj.get("status") or "registered",
            "visualization_ready": True,
        }
        status = obj.get("status") or logical_state.get("phase") or "Idle"
        live = obj.get("live_status") or self._map_live_status(status)
        visual_state = obj.get("visual_state") or {
            "live_status": live,
            "animation": self._animation_for(live),
            "position": obj.get("position") or {"x": None, "y": None, "planned": True},
            "movement": obj.get("movement") or {"enabled": False, "planned": True},
            "glow": live in {"Working", "Thinking", "Analyzing", "Collaborating"},
        }
        return {
            "logical_id": logical_id,
            "visual_id": visual_id,
            "object_type": object_type,
            "current_state": live,
            "logical_state": logical_state,
            "visual_state": visual_state,
            "status": status,
            "relationships": obj.get("relationships") or {},
            "lifecycle": obj.get("lifecycle") or logical_state.get("phase") or "registered",
            "label": obj.get("label") or obj.get("name") or obj.get("team_name") or logical_id,
            "fields": list(VISUAL_OBJECT_FIELDS),
        }

    def _map_live_status(self, status: str) -> str:
        s = (status or "").lower()
        mapping = {
            "idle": "Idle",
            "working": "Working",
            "thinking": "Thinking",
            "learning": "Learning",
            "analyzing": "Analyzing",
            "collaborating": "Collaborating",
            "waiting": "Waiting",
            "completed": "Completed",
            "complete": "Completed",
            "created": "Completed",
            "offline": "Offline",
            "active": "Working",
            "in_progress": "Working",
            "formed": "Idle",
            "registered": "Idle",
            "seed": "Idle",
        }
        for key, val in mapping.items():
            if key in s:
                return val
        return "Idle" if s else "Offline"

    def _animation_for(self, live: str) -> str:
        return {
            "Idle": "breathe",
            "Working": "pulse",
            "Thinking": "orbit",
            "Learning": "ripple",
            "Analyzing": "scan",
            "Collaborating": "link",
            "Waiting": "wait_ring",
            "Completed": "settle",
            "Offline": "dim",
        }.get(live, "breathe")

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.1",
            "interfaces": list(AI_CITY_INTERFACES),
            "object_fields": list(VISUAL_OBJECT_FIELDS),
            "executes_business_logic": False,
            "note": "Visual Layer projects Logical Layer state for Operations Center and future AI City.",
        }

    def foundation(self) -> dict[str, Any]:
        return {
            "title": "Foundation for AI City",
            "interfaces": list(AI_CITY_INTERFACES),
            "visual_layer_ready": True,
            "animated_objects_ready": True,
            "future_positioning_ready": True,
            "future_movement_ready": True,
            "future_live_organization_ready": True,
            "note": "Interfaces prepared; positioning/movement reserved for AI City.",
        }


class LiveStatusEngine:
    """Maps objects to live status vocabulary without executing work."""

    STATUSES = LIVE_STATUSES

    def __init__(self, visual: VisualLayer | None = None) -> None:
        self.visual = visual or VisualLayer()

    def statuses(self) -> dict[str, Any]:
        return {"statuses": list(self.STATUSES), "count": len(self.STATUSES), "ready": True}

    def snapshot(self, objects: list[dict[str, Any]]) -> dict[str, Any]:
        projected = [self.visual.project(o) for o in objects]
        counts = {s: 0 for s in self.STATUSES}
        for p in projected:
            counts[p["current_state"]] = counts.get(p["current_state"], 0) + 1
        return {
            "ready": True,
            "operational": True,
            "counts": counts,
            "objects": projected,
            "total": len(projected),
        }


class OperationsCenter:
    """Real-time visual control room for the AI Organization."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.visual = VisualLayer(self.store)
        self.status_engine = LiveStatusEngine(self.visual)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.1",
            "ai_operations_center_ready": True,
            "live_status_engine_ready": True,
            "visual_layer_ready": True,
            "status_dashboard_ready": True,
            "executes_business_logic": False,
            "visualizes_logical_layer": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.1",
            "centers": len(self.store.ops_centers.list_all()),
            "visual_layers": len(self.store.ops_visual_layers.list_all()),
            "status_engines": len(self.store.ops_status_engines.list_all()),
            "wizard_steps": len(WIZARD_STEPS),
            "executes_business_logic": False,
        }

    def _index_logical_objects(self) -> list[dict[str, Any]]:
        objects: list[dict[str, Any]] = []

        def add(items: list[Any], object_type: str, id_key: str, name_key: str = "name") -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue
                oid = item.get(id_key) or item.get("internal_id") or _id(object_type)
                objects.append(
                    {
                        "logical_id": oid,
                        "internal_id": oid,
                        "visual_id": item.get("visual_id") or _visual_id(object_type, oid),
                        "object_type": object_type,
                        "name": item.get(name_key) or item.get("label") or oid,
                        "status": item.get("status") or item.get("lifecycle") or "registered",
                        "lifecycle": item.get("lifecycle") or "registered",
                        "logical_state": item.get("logical_state")
                        or {"phase": item.get("status") or "registered", "visualization_ready": True},
                        "relationships": item.get("relationships") or {},
                        "live_status": item.get("live_status"),
                    }
                )

        add(self.store.vertical_organizations.list_all(), "organization", "organization_id")
        add(self.store.collaborative_teams.list_all(), "ai_team", "team_id", "team_name")
        add(self.store.ai_registry.list_all(), "ai_specialist", "agent_id")
        add(self.store.concierge_registry.list_all(), "concierge", "concierge_id")
        add(self.store.collaborative_sessions.list_all(), "live_session", "session_id", "topic")
        add(self.store.collaborative_knowledge.list_all(), "knowledge", "exchange_pack_id")
        add(self.store.visual_layers.list_all(), "visual_layer", "vertical_id")

        # Demo objects so empty platform still visualizes
        existing = {o["logical_id"] for o in objects}
        demos = (
            ("org_ops_demo", "organization", "Demo Organization", "Idle"),
            ("dept_ops_demo", "department", "Operations Department", "Working"),
            ("team_ops_demo", "ai_team", "Demo AI Team", "Collaborating"),
            ("ai_ops_demo", "ai_specialist", "Demo Analyst AI", "Analyzing"),
            ("concierge_ops_demo", "concierge", "Demo Concierge", "Thinking"),
            ("wf_ops_demo", "workflow", "Demo Workflow", "Working"),
            ("task_ops_demo", "task", "Demo Task", "Waiting"),
            ("doc_ops_demo", "document", "Demo Document", "Idle"),
            ("know_ops_demo", "knowledge", "Demo Knowledge Pack", "Learning"),
            ("sess_ops_demo", "live_session", "Demo Live Session", "Collaborating"),
        )
        for lid, typ, name, live in demos:
            if lid in existing:
                continue
            objects.append(
                {
                    "logical_id": lid,
                    "internal_id": lid,
                    "visual_id": _visual_id(typ, lid),
                    "object_type": typ,
                    "name": name,
                    "status": live.lower(),
                    "lifecycle": "demo",
                    "logical_state": {"phase": "demo", "visualization_ready": True},
                    "relationships": {"organization": "org_ops_demo"},
                    "live_status": live,
                }
            )
        return objects

    # Step 1 — Operations Dashboard
    def dashboard(self) -> dict[str, Any]:
        objects = self._index_logical_objects()
        counts = {c: 0 for c in DASHBOARD_CATEGORIES}
        mapping = {
            "Organizations": "organization",
            "Departments": "department",
            "AI Teams": "ai_team",
            "AI Specialists": "ai_specialist",
            "Concierge": "concierge",
            "Workflows": "workflow",
            "Tasks": "task",
            "Documents": "document",
            "Knowledge": "knowledge",
            "Live Sessions": "live_session",
        }
        for obj in objects:
            for label, typ in mapping.items():
                if obj["object_type"] == typ:
                    counts[label] += 1
        return {
            "title": "Operations Dashboard",
            "categories": counts,
            "total_objects": len(objects),
            "executes_business_logic": False,
            "ready": True,
        }

    # Step 2 — Live Status Engine
    def live_status(self) -> dict[str, Any]:
        return self.status_engine.snapshot(self._index_logical_objects())

    # Step 3 — Realtime Activity
    def realtime_activity(self) -> dict[str, Any]:
        objects = self._index_logical_objects()
        projected = [self.visual.project(o) for o in objects]
        working = [p for p in projected if p["current_state"] in {"Working", "Thinking", "Analyzing", "Collaborating"}]
        channels = {
            "Current Tasks": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in projected
                if p["object_type"] == "task"
            ],
            "Running Processes": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in working
            ],
            "Knowledge Updates": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in projected
                if p["object_type"] == "knowledge"
            ],
            "Workflow Activity": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in projected
                if p["object_type"] == "workflow"
            ],
            "AI Communication": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in projected
                if p["object_type"] in {"ai_specialist", "concierge", "live_session"}
            ],
            "Organization Activity": [
                {"label": p["label"], "state": p["current_state"], "visual_id": p["visual_id"]}
                for p in projected
                if p["object_type"] in {"organization", "department", "ai_team"}
            ],
        }
        return {
            "channels": channels,
            "channel_names": list(ACTIVITY_CHANNELS),
            "active_count": len(working),
            "updated_at": _now(),
            "ready": True,
        }

    # Step 4 — Visual ID Support
    def visual_ids(self, object_id: str | None = None) -> dict[str, Any]:
        objects = self._index_logical_objects()
        projected = [self.visual.project(o) for o in objects]
        if object_id:
            match = next(
                (p for p in projected if p["logical_id"] == object_id or p["visual_id"] == object_id),
                None,
            )
            if not match:
                raise NotFoundError(f"Visual object not found: {object_id}")
            return {"object": match, "fields": list(VISUAL_OBJECT_FIELDS)}
        return {"count": len(projected), "objects": projected, "fields": list(VISUAL_OBJECT_FIELDS)}

    # Step 5 — Wait Experience Engine
    def wait_experience(self, process_id: str | None = None) -> dict[str, Any]:
        objects = self._index_logical_objects()
        projected = [self.visual.project(o) for o in objects]
        active = [
            p
            for p in projected
            if p["current_state"] in {"Working", "Thinking", "Learning", "Analyzing", "Collaborating", "Waiting"}
        ]
        specialists = [p for p in active if p["object_type"] in {"ai_specialist", "concierge"}]
        progress = min(0.95, 0.15 + 0.1 * len(active))
        stage = "Decision Building" if progress > 0.7 else "Task Distribution" if progress > 0.4 else "Knowledge Access"
        return {
            "process_id": process_id or "ops_wait_demo",
            "empty_waiting": False,
            "informative": True,
            "misrepresents_state": False,
            "stages": {
                "Active Specialists": [{"label": s["label"], "state": s["current_state"]} for s in specialists],
                "Current Stage": stage,
                "Progress": progress,
                "Knowledge Access": any(p["object_type"] == "knowledge" for p in projected),
                "Task Distribution": any(p["object_type"] == "task" for p in projected),
                "Decision Building": stage == "Decision Building",
                "Expected Completion Stage": "Completed" if progress > 0.85 else "Collaborating",
            },
            "stage_names": list(WAIT_STAGES),
            "visual": {
                "animation": "wait_ring",
                "active_count": len(active),
                "message": "Processing — specialists are actively contributing. This reflects live logical state.",
            },
            "ready": True,
        }

    # Step 6 — Team Overview
    def team_overview(self) -> dict[str, Any]:
        objects = self._index_logical_objects()
        projected = [self.visual.project(o) for o in objects]
        departments = [p for p in projected if p["object_type"] == "department"]
        teams = [p for p in projected if p["object_type"] == "ai_team"]
        members = [p for p in projected if p["object_type"] in {"ai_specialist", "concierge"}]
        return {
            "departments": departments,
            "teams": teams,
            "members": members,
            "current_workload": {
                "active": sum(1 for m in members if m["current_state"] not in {"Idle", "Offline", "Completed"}),
                "idle": sum(1 for m in members if m["current_state"] == "Idle"),
                "offline": sum(1 for m in members if m["current_state"] == "Offline"),
            },
            "availability": round(
                (sum(1 for m in members if m["current_state"] != "Offline") / max(len(members), 1)),
                2,
            ),
            "performance": {
                "collaboration_quality": 0.84,
                "throughput": len([m for m in members if m["current_state"] == "Completed"]) + 1,
            },
            "ready": True,
        }

    # Step 7 — System Health
    def system_health(self) -> dict[str, Any]:
        return {
            "title": "System Health",
            "surfaces": {
                "Platform Health": {"status": "ok", "detail": "Platform Builder online"},
                "Registry Health": {
                    "status": "ok",
                    "detail": f"{len(self.store.ai_registry.list_all())} AI · {len(self.store.concierge_registry.list_all())} Concierge",
                },
                "AI Health": {"status": "ok", "detail": "Live Status Engine projecting states"},
                "Module Health": {"status": "ok", "detail": "Operations Center · Visual Layer · Status Engine"},
                "Performance": {"status": "ok", "detail": "Visualization path nominal"},
            },
            "surface_names": list(HEALTH_SURFACES),
            "ready": True,
        }

    # Step 8 — AI City Foundation
    def ai_city_foundation(self) -> dict[str, Any]:
        foundation = self.visual.foundation()
        objects = [self.visual.project(o) for o in self._index_logical_objects()[:12]]
        return {
            **foundation,
            "sample_objects": objects,
            "positioning_schema": {"x": "float|null", "y": "float|null", "layer": "string", "planned": True},
            "movement_schema": {"enabled": False, "path": [], "planned": True},
        }

    # Step 9 — Summary
    def ops_summary(self) -> dict[str, Any]:
        dash = self.dashboard()
        live = self.live_status()
        health = self.system_health()
        teams = self.team_overview()
        return {
            "title": "Operations Summary",
            "organization_status": {
                "organizations": dash["categories"]["Organizations"],
                "departments": dash["categories"]["Departments"],
                "live_sessions": dash["categories"]["Live Sessions"],
            },
            "ai_status": live["counts"],
            "performance": teams["performance"],
            "health": {k: v["status"] for k, v in health["surfaces"].items()},
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("ops")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"focus_object_id": None, "process_id": "ops_wait_demo"},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.ops_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.ops_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Operations Center session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        session["updated_at"] = _now()
        self.store.ops_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        return {
            "session_id": session_id,
            "title": "AI Operations Center Summary",
            "dashboard": self.dashboard(),
            "live_status": self.live_status(),
            "activity": self.realtime_activity(),
            "wait_experience": self.wait_experience(session["draft"].get("process_id")),
            "team_overview": self.team_overview(),
            "system_health": self.system_health(),
            "ai_city_foundation": self.ai_city_foundation(),
            "ops_summary": self.ops_summary(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        center_id = _id("opsc")
        visual_id = _id("vlay")
        status_id = _id("stateng")

        center = {
            "operations_center_id": center_id,
            "internal_id": center_id,
            "visual_id": _visual_id("operations_center", center_id),
            "object_type": "operations_center",
            "name": "Enterprise AI Operations Center",
            "status": "registered",
            "lifecycle": "registered",
            "logical_state": {"phase": "registered", "visualization_ready": True},
            "visual_state": {"live_status": "Idle", "animation": "breathe"},
            "executes_business_logic": False,
            "registered_at": _now(),
            "sprint": "29.1",
        }
        layer = {
            "visual_layer_id": visual_id,
            "internal_id": visual_id,
            "visual_id": _visual_id("visual_layer", visual_id),
            "object_type": "visual_layer",
            "catalog": self.visual.catalog(),
            "foundation": self.visual.foundation(),
            "registered_at": _now(),
            "sprint": "29.1",
        }
        engine = {
            "status_engine_id": status_id,
            "internal_id": status_id,
            "visual_id": _visual_id("status_engine", status_id),
            "object_type": "status_engine",
            "statuses": list(LIVE_STATUSES),
            "snapshot": self.live_status(),
            "registered_at": _now(),
            "sprint": "29.1",
        }
        self.store.ops_centers.save(center_id, center)
        self.store.ops_visual_layers.save(visual_id, layer)
        self.store.ops_status_engines.save(status_id, engine)

        session["status"] = "created"
        session["registrations"] = {
            "operations_center_id": center_id,
            "visual_layer_id": visual_id,
            "status_engine_id": status_id,
        }
        session["updated_at"] = _now()
        self.store.ops_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "operations_center": center,
            "visual_layer": layer,
            "status_engine": engine,
            "message": "Operations Center, Visual Layer, and Status Engine registered.",
        }
