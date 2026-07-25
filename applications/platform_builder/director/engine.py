"""Visual Director Engine & Intelligent Scene Orchestration — Sprint 29.8.

Coordinates all visual activity across the platform.
Does not generate business events — orchestrates visual presentation only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.director.catalogs import (
    ATTENTION_COORDINATION,
    CAMERA_API,
    CONFLICT_PREVENTIONS,
    COORDINATED_ENGINES,
    DIRECTOR_COMPONENTS,
    FOCUS_TARGETS,
    LIVE_ORG_DIRECTIVES,
    PERF_FEATURES,
    SCENE_FEATURES,
    SCENE_LIFECYCLE,
    UI_SURFACES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.team_map.engine import VisualEventBus


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class PriorityManager:
    """Ranks visual presentation priorities — not business priorities."""

    def rank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        weight = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(candidates, key=lambda c: weight.get(c.get("priority") or "medium", 2))

    def timeline(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = self.rank(items)
        return {
            "timeline": ranked,
            "count": len(ranked),
            "ready": True,
        }


class FocusManager:
    """Automatically determines visual focus targets."""

    def resolve(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = signals or {}
        scored = [
            {
                "target": "Highest Priority AI",
                "score": float(signals.get("ai_priority", 0.9)),
                "ref": signals.get("ai_ref") or "ai_specialist_1",
            },
            {
                "target": "Most Active Department",
                "score": float(signals.get("dept_activity", 0.75)),
                "ref": signals.get("dept_ref") or "dept_ops",
            },
            {
                "target": "Critical Workflow",
                "score": float(signals.get("workflow_critical", 0.85)),
                "ref": signals.get("workflow_ref") or "wf_live_1",
            },
            {
                "target": "Urgent Notification",
                "score": float(signals.get("notification_urgency", 0.7)),
                "ref": signals.get("notif_ref") or "notif_1",
            },
            {
                "target": "Current Decision Point",
                "score": float(signals.get("decision_weight", 0.8)),
                "ref": signals.get("decision_ref") or "decision_1",
            },
            {
                "target": "Organization Highlights",
                "score": float(signals.get("org_highlight", 0.6)),
                "ref": signals.get("org_ref") or "org_default",
            },
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        primary = scored[0]
        return {
            "targets": list(FOCUS_TARGETS),
            "ranked": scored,
            "primary_focus": primary,
            "live_focus_indicator": {
                "target": primary["target"],
                "ref": primary["ref"],
                "score": primary["score"],
            },
            "generates_business_events": False,
            "ready": True,
        }


class AttentionManager:
    def coordinate(self, focus: dict[str, Any]) -> dict[str, Any]:
        primary = focus.get("primary_focus") or {}
        queue = [
            {
                "kind": kind,
                "target": primary.get("ref"),
                "focus_label": primary.get("target"),
                "scheduled": True,
            }
            for kind in ATTENTION_COORDINATION
        ]
        return {
            "coordination": list(ATTENTION_COORDINATION),
            "attention_queue": queue,
            "current_highlight": {
                "ref": primary.get("ref"),
                "label": primary.get("target"),
                "style": "pulse-outline",
            },
            "notification_timing": {"stagger_ms": 180, "max_concurrent": 2},
            "ready": True,
        }


class SceneDirector:
    """Scene lifecycle and switching — presentation state only."""

    def __init__(self, store: PlatformBuilderStore) -> None:
        self.store = store
        self.active_scene_id: str | None = None

    def create_scene(self, name: str, *, kind: str = "live_organization") -> dict[str, Any]:
        sid = _id("scene")
        record = {
            "scene_id": sid,
            "name": name,
            "kind": kind,
            "state": "created",
            "lifecycle": list(SCENE_LIFECYCLE),
            "synced_engines": [],
            "created_at": _now(),
            "updated_at": _now(),
            "generates_business_events": False,
        }
        self.store.director_scenes.save(sid, record)
        return record

    def get_scene(self, scene_id: str) -> dict[str, Any]:
        scene = self.store.director_scenes.get(scene_id)
        if not scene:
            raise NotFoundError(f"Scene not found: {scene_id}")
        return scene

    def switch_scene(self, scene_id: str) -> dict[str, Any]:
        scene = self.get_scene(scene_id)
        # pause previous
        if self.active_scene_id and self.active_scene_id != scene_id:
            prev = self.store.director_scenes.get(self.active_scene_id)
            if prev:
                prev["state"] = "paused"
                prev["updated_at"] = _now()
                self.store.director_scenes.save(self.active_scene_id, prev)
        scene["state"] = "active"
        scene["updated_at"] = _now()
        self.store.director_scenes.save(scene_id, scene)
        self.active_scene_id = scene_id
        return {"ok": True, "active_scene": scene, "action": "Scene Switching"}

    def synchronize(self, scene_id: str, engines: list[str] | None = None) -> dict[str, Any]:
        scene = self.get_scene(scene_id)
        engines = engines or list(COORDINATED_ENGINES)
        scene["synced_engines"] = engines
        scene["state"] = "synchronized"
        scene["updated_at"] = _now()
        self.store.director_scenes.save(scene_id, scene)
        return {"ok": True, "scene": scene, "action": "Scene Synchronization"}

    def list_scenes(self) -> dict[str, Any]:
        scenes = self.store.director_scenes.list_all()
        return {
            "scenes": scenes,
            "count": len(scenes),
            "active_scene_id": self.active_scene_id,
            "features": list(SCENE_FEATURES),
            "ready": True,
        }


class VisualDirectorEngine:
    """Enterprise Visual Director — presentation orchestration only."""

    def __init__(
        self,
        store: PlatformBuilderStore | None = None,
        bus: VisualEventBus | None = None,
    ) -> None:
        self.store = store or platform_builder_store
        self.bus = bus or VisualEventBus(self.store)
        self.scenes = SceneDirector(self.store)
        self.focus = FocusManager()
        self.attention = AttentionManager()
        self.priority = PriorityManager()
        self._camera = {
            "position": {"x": 0, "y": 0, "z": 1},
            "tracking": None,
            "smooth_follow": True,
            "zoom_target": 1.0,
            "focus_target": None,
        }
        self._ensure_default_scene()

    def _ensure_default_scene(self) -> None:
        if not self.store.director_scenes.list_all():
            scene = self.scenes.create_scene("Executive Overview", kind="executive")
            self.scenes.switch_scene(scene["scene_id"])

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.8",
            "director_engine_ready": True,
            "scene_manager_ready": True,
            "focus_engine_ready": True,
            "priority_manager_ready": True,
            "generates_business_events": False,
            "orchestrates_visual_presentation_only": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.8",
            "generates_business_events": False,
            "orchestrates_visual_presentation_only": True,
            "components": list(DIRECTOR_COMPONENTS),
            "scenes": self.scenes.list_scenes()["count"],
            "active_scene_id": self.scenes.active_scene_id,
            "director_engines": len(self.store.director_engines.list_all()),
        }

    # Step 1
    def director_overview(self) -> dict[str, Any]:
        return {
            "title": "Director Engine",
            "components": list(DIRECTOR_COMPONENTS),
            "status": self.status(),
            "generates_business_events": False,
            "orchestrates_visual_presentation_only": True,
            "ready": True,
        }

    # Step 2
    def scene_management(self) -> dict[str, Any]:
        return {
            **self.scenes.list_scenes(),
            "lifecycle": list(SCENE_LIFECYCLE),
            "features": list(SCENE_FEATURES),
            "scene_status": {
                "active_scene_id": self.scenes.active_scene_id,
                "count": self.scenes.list_scenes()["count"],
            },
        }

    # Step 3
    def focus_engine(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        # Optionally bias from visual bus event volume (presentation signal only)
        polled = self.bus.poll(limit=20)
        channels = {}
        for e in polled.get("events") or []:
            ch = e.get("channel") or "unknown"
            channels[ch] = channels.get(ch, 0) + 1
        auto = {
            "ai_priority": 0.5 + min(0.45, channels.get("AI Events", 0) * 0.05),
            "workflow_critical": 0.5 + min(0.45, channels.get("Workflow Events", 0) * 0.05),
            "dept_activity": 0.5 + min(0.4, channels.get("Organization Events", 0) * 0.05),
            "notification_urgency": 0.55,
            "decision_weight": 0.7,
            "org_highlight": 0.6,
        }
        if signals:
            auto.update(signals)
        result = self.focus.resolve(auto)
        if result["primary_focus"]:
            self._camera["focus_target"] = result["primary_focus"]["ref"]
        return result

    # Step 4
    def attention_management(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        focus = self.focus_engine(signals)
        return self.attention.coordinate(focus)

    # Step 5 — coordinate engines (presentation sync only)
    def simulation_coordination(self, scene_id: str | None = None) -> dict[str, Any]:
        sid = scene_id or self.scenes.active_scene_id
        if not sid:
            scene = self.scenes.create_scene("Coordination Scene")
            sid = scene["scene_id"]
            self.scenes.switch_scene(sid)
        synced = self.scenes.synchronize(sid, list(COORDINATED_ENGINES))
        return {
            "engines": list(COORDINATED_ENGINES),
            "coordination": {name: {"linked": True, "role": "presentation"} for name in COORDINATED_ENGINES},
            "scene": synced["scene"],
            "generates_business_events": False,
            "note": "Director orchestrates presentation; does not emit business events.",
            "ready": True,
        }

    # Step 6
    def live_organization(self) -> dict[str, Any]:
        focus = self.focus_engine()
        return {
            "directives": list(LIVE_ORG_DIRECTIVES),
            "directed": {
                name: {
                    "active": True,
                    "focus_ref": focus["primary_focus"]["ref"],
                    "presentation_only": True,
                }
                for name in LIVE_ORG_DIRECTIVES
            },
            "primary_focus": focus["primary_focus"],
            "generates_business_events": False,
            "ready": True,
        }

    # Step 7
    def camera_api(
        self,
        *,
        position: dict[str, float] | None = None,
        tracking: str | None = None,
        zoom: float | None = None,
        focus_target: str | None = None,
    ) -> dict[str, Any]:
        if position:
            self._camera["position"] = {**self._camera["position"], **position}
        if tracking is not None:
            self._camera["tracking"] = tracking
        if zoom is not None:
            self._camera["zoom_target"] = float(zoom)
        if focus_target is not None:
            self._camera["focus_target"] = focus_target
        return {
            "api": list(CAMERA_API),
            "camera": dict(self._camera),
            "smooth_follow": True,
            "future_ai_city_navigation": {"ready": True, "planned": True},
            "generates_business_events": False,
            "ready": True,
        }

    # Step 8
    def conflict_resolution(self) -> dict[str, Any]:
        attention = self.attention_management()
        # Cap concurrent highlights / notifications (presentation conflict prevention)
        queue = attention["attention_queue"][:3]
        return {
            "preventions": list(CONFLICT_PREVENTIONS),
            "active_rules": {p: True for p in CONFLICT_PREVENTIONS},
            "resolved_queue": queue,
            "max_concurrent_highlights": 1,
            "max_concurrent_notifications": 2,
            "animation_collision_guard": True,
            "ready": True,
        }

    # Step 9
    def performance(self) -> dict[str, Any]:
        return {
            "features": {f: True for f in PERF_FEATURES},
            "feature_names": list(PERF_FEATURES),
            "adaptive_rendering": True,
            "priority_scheduling": True,
            "viewport_awareness": True,
            "resource_coordination": True,
            "gpu_optimized": True,
            "ready": True,
        }

    # UI
    def ui_dashboard(self) -> dict[str, Any]:
        focus = self.focus_engine()
        attention = self.attention.coordinate(focus)
        priority_items = [
            {"id": r["ref"], "label": r["target"], "priority": "high" if r["score"] >= 0.8 else "medium"}
            for r in focus["ranked"]
        ]
        return {
            "surfaces": list(UI_SURFACES),
            "live_focus_indicator": focus["live_focus_indicator"],
            "scene_status": self.scene_management()["scene_status"],
            "attention_queue": attention["attention_queue"],
            "current_highlight": attention["current_highlight"],
            "priority_timeline": self.priority.timeline(priority_items),
            "generates_business_events": False,
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("dir")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"scene_name": "Live Ops"},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.director_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.director_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Director session not found: {session_id}")
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
        self.store.director_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Visual Director Engine Summary",
            "director": self.director_overview(),
            "scenes": self.scene_management(),
            "focus": self.focus_engine(),
            "attention": self.attention_management(),
            "coordination": self.simulation_coordination(),
            "live_organization": self.live_organization(),
            "camera": self.camera_api(),
            "conflicts": self.conflict_resolution(),
            "performance": self.performance(),
            "ui": self.ui_dashboard(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        name = session["draft"].get("scene_name") or "Directed Scene"
        scene = self.scenes.create_scene(name)
        self.scenes.switch_scene(scene["scene_id"])
        self.simulation_coordination(scene["scene_id"])

        dir_id = _id("vdeng")
        sm_id = _id("vscnm")
        fm_id = _id("vfocm")
        pm_id = _id("vpriom")

        director_engine = {
            "director_engine_id": dir_id,
            "internal_id": dir_id,
            "catalog": self.catalog(),
            "generates_business_events": False,
            "orchestrates_visual_presentation_only": True,
            "registered_at": _now(),
            "sprint": "29.8",
        }
        scene_manager = {
            "scene_manager_id": sm_id,
            "internal_id": sm_id,
            "active_scene_id": scene["scene_id"],
            "features": list(SCENE_FEATURES),
            "registered_at": _now(),
            "sprint": "29.8",
        }
        focus_manager = {
            "focus_manager_id": fm_id,
            "internal_id": fm_id,
            "targets": list(FOCUS_TARGETS),
            "registered_at": _now(),
            "sprint": "29.8",
        }
        priority_manager = {
            "priority_manager_id": pm_id,
            "internal_id": pm_id,
            "ready": True,
            "registered_at": _now(),
            "sprint": "29.8",
        }

        self.store.director_engines.save(dir_id, director_engine)
        self.store.scene_managers.save(sm_id, scene_manager)
        self.store.focus_managers.save(fm_id, focus_manager)
        self.store.priority_managers.save(pm_id, priority_manager)

        # Presentation registry signal only — not a business event
        self.bus.publish(
            "Registry Events",
            "director_engine_registered",
            {"director_engine_id": dir_id, "presentation_only": True},
        )

        session["status"] = "created"
        session["registrations"] = {
            "director_engine_id": dir_id,
            "scene_manager_id": sm_id,
            "focus_manager_id": fm_id,
            "priority_manager_id": pm_id,
            "scene_id": scene["scene_id"],
        }
        session["updated_at"] = _now()
        self.store.director_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "director_engine": director_engine,
            "scene_manager": scene_manager,
            "focus_manager": focus_manager,
            "priority_manager": priority_manager,
            "scene": scene,
            "message": "Director Engine, Scene Manager, Focus Manager, and Priority Manager registered.",
        }
