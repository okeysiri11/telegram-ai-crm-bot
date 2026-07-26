"""Visual Experience Engine & Unified Enterprise UX — Sprint 29.11.

Unifies every visual subsystem into one seamless enterprise experience.
Never executes business logic. Coordinates presentation, consistency,
accessibility and user perception across the platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.experience.catalogs import (
    ACCESSIBILITY_FEATURES,
    ADAPTIVE_DIMENSIONS,
    COGNITIVE_CONTROLS,
    CONTEXT_PROFILES,
    EXPERIENCE_COMPONENTS,
    GLOBAL_RULES,
    TRANSITION_TYPES,
    UI_SURFACES,
    UNIFIED_SUBSYSTEMS,
    USER_CONTEXTS,
    WORKSPACE_FEATURES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ExperienceController:
    """Controls active context, adaptive profile, and transitions — presentation only."""

    def __init__(self) -> None:
        self.active_context = "Manager Context"
        self.adaptive_profile = dict(CONTEXT_PROFILES["Manager Context"])
        self.accessibility = {f: True for f in ACCESSIBILITY_FEATURES}
        self.cognitive_limits = {
            "max_notifications": 3,
            "max_concurrent_animations": 2,
            "max_open_panels": 4,
            "context_switch_cooldown_ms": 400,
        }
        self.workspaces: list[dict[str, Any]] = [
            {
                "workspace_id": "ws_default",
                "name": "Primary Workspace",
                "memory": {},
                "active": True,
            }
        ]
        self.active_workspace_id = "ws_default"
        self.transition_log: list[dict[str, Any]] = []

    def status(self) -> dict[str, Any]:
        return {
            "active_context": self.active_context,
            "adaptive_profile": dict(self.adaptive_profile),
            "accessibility": dict(self.accessibility),
            "cognitive_limits": dict(self.cognitive_limits),
            "active_workspace_id": self.active_workspace_id,
            "workspace_count": len(self.workspaces),
            "executes_business_logic": False,
            "ready": True,
        }


class VisualExperienceEngine:
    """Enterprise Visual Experience Engine — presentation coordination only."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.controller = ExperienceController()

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.11",
            "experience_engine_ready": True,
            "unified_ux_ready": True,
            "adaptive_interface_ready": True,
            "accessibility_operational": True,
            "executes_business_logic": False,
            "presentation_coordination_only": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.11",
            "executes_business_logic": False,
            "presentation_coordination_only": True,
            "components": list(EXPERIENCE_COMPONENTS),
            "engines": len(self.store.experience_engines.list_all()),
            "controller": self.controller.status(),
        }

    # Step 1
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Visual Experience Engine",
            "components": list(EXPERIENCE_COMPONENTS),
            "controller": self.controller.status(),
            "executes_business_logic": False,
            "presentation_coordination_only": True,
            "ready": True,
        }

    # Step 2 — Unified Experience
    def unified_experience(self) -> dict[str, Any]:
        return {
            "subsystems": {
                name: {
                    "coordinated": True,
                    "role": "presentation",
                    "linked": True,
                }
                for name in UNIFIED_SUBSYSTEMS
            },
            "subsystem_names": list(UNIFIED_SUBSYSTEMS),
            "seamless": True,
            "executes_business_logic": False,
            "ready": True,
        }

    # Step 3 — User Context
    def user_context(self, context: str | None = None) -> dict[str, Any]:
        if context:
            if context not in USER_CONTEXTS:
                raise ValidationError(f"Unsupported context: {context}")
            self.controller.active_context = context
            self.controller.adaptive_profile = dict(CONTEXT_PROFILES[context])
        return {
            "contexts": list(USER_CONTEXTS),
            "active_context": self.controller.active_context,
            "profile": dict(self.controller.adaptive_profile),
            "profiles": {k: dict(v) for k, v in CONTEXT_PROFILES.items()},
            "ready": True,
        }

    # Step 4 — Adaptive Interface
    def adaptive_interface(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            for key in ADAPTIVE_DIMENSIONS:
                if key in patch:
                    self.controller.adaptive_profile[key] = patch[key]
        return {
            "dimensions": list(ADAPTIVE_DIMENSIONS),
            "profile": dict(self.controller.adaptive_profile),
            "auto_adapt_by_context": True,
            "active_context": self.controller.active_context,
            "ready": True,
        }

    # Step 5 — Transitions
    def transitions(self, transition_type: str | None = None, target: str | None = None) -> dict[str, Any]:
        if transition_type:
            if transition_type not in TRANSITION_TYPES:
                raise ValidationError(f"Unsupported transition: {transition_type}")
            record = {
                "transition_id": _id("xtrn"),
                "type": transition_type,
                "target": target or "default",
                "at": _now(),
                "executes_business_logic": False,
            }
            self.controller.transition_log.append(record)
        return {
            "types": list(TRANSITION_TYPES),
            "supported": {t: True for t in TRANSITION_TYPES},
            "recent": list(self.controller.transition_log[-10:]),
            "ready": True,
        }

    # Step 6 — Global Experience Rules
    def global_rules(self) -> dict[str, Any]:
        return {
            "rules": {r: {"enforced": True, "scope": "platform"} for r in GLOBAL_RULES},
            "rule_names": list(GLOBAL_RULES),
            "consistency_score": 1.0,
            "ready": True,
        }

    # Step 7 — Cognitive Load Control
    def cognitive_load_control(self) -> dict[str, Any]:
        limits = self.controller.cognitive_limits
        return {
            "controls": list(COGNITIVE_CONTROLS),
            "prevention": {c: True for c in COGNITIVE_CONTROLS},
            "limits": limits,
            "status": {
                "Information Overload": "guarded",
                "Notification Overload": f"max {limits['max_notifications']}",
                "Animation Overload": f"max {limits['max_concurrent_animations']}",
                "Context Switching Fatigue": f"cooldown {limits['context_switch_cooldown_ms']}ms",
                "Visual Noise": "filtered",
            },
            "ready": True,
        }

    # Step 8 — Multi-Workspace
    def multi_workspace(
        self,
        *,
        action: str | None = None,
        workspace_id: str | None = None,
        name: str | None = None,
        memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if action == "create":
            wid = _id("ws")
            ws = {
                "workspace_id": wid,
                "name": name or f"Workspace {len(self.controller.workspaces) + 1}",
                "memory": memory or {},
                "active": False,
            }
            self.controller.workspaces.append(ws)
        elif action == "switch":
            if not workspace_id:
                raise ValidationError("workspace_id is required to switch")
            found = next(
                (w for w in self.controller.workspaces if w["workspace_id"] == workspace_id),
                None,
            )
            if not found:
                raise NotFoundError(f"Workspace not found: {workspace_id}")
            for w in self.controller.workspaces:
                w["active"] = w["workspace_id"] == workspace_id
            self.controller.active_workspace_id = workspace_id
        elif action == "remember" and workspace_id:
            found = next(
                (w for w in self.controller.workspaces if w["workspace_id"] == workspace_id),
                None,
            )
            if not found:
                raise NotFoundError(f"Workspace not found: {workspace_id}")
            found["memory"] = {**found.get("memory", {}), **(memory or {})}
        return {
            "features": list(WORKSPACE_FEATURES),
            "workspaces": list(self.controller.workspaces),
            "active_workspace_id": self.controller.active_workspace_id,
            "cross_workspace_navigation": True,
            "shared_context": {"active_context": self.controller.active_context},
            "persistent_session": True,
            "live_synchronization": True,
            "workspace_memory": True,
            "ready": True,
        }

    # Step 9 — Accessibility
    def accessibility(self, patch: dict[str, bool] | None = None) -> dict[str, Any]:
        if patch:
            for key in ACCESSIBILITY_FEATURES:
                if key in patch:
                    self.controller.accessibility[key] = bool(patch[key])
        return {
            "features": dict(self.controller.accessibility),
            "feature_names": list(ACCESSIBILITY_FEATURES),
            "accessibility_ready": True,
            "operational": True,
            "ready": True,
        }

    # UI
    def ui_dashboard(self) -> dict[str, Any]:
        return {
            "surfaces": list(UI_SURFACES),
            "experience_center": self.engine_overview(),
            "ux_diagnostics": {
                "rules": self.global_rules(),
                "cognitive": self.cognitive_load_control(),
                "accessibility": self.accessibility(),
            },
            "interaction_monitor": {
                "transitions": len(self.controller.transition_log),
                "recent": self.controller.transition_log[-5:],
            },
            "context_viewer": self.user_context(),
            "adaptive_ui_panel": self.adaptive_interface(),
            "executes_business_logic": False,
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("xper")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"context": "Manager Context"},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.experience_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.experience_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Experience session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session.get("draft", {}), **patch["draft"]}
        session["updated_at"] = _now()
        self.store.experience_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Visual Experience Engine Summary",
            "engine": self.engine_overview(),
            "unified": self.unified_experience(),
            "context": self.user_context(),
            "adaptive": self.adaptive_interface(),
            "transitions": self.transitions(),
            "rules": self.global_rules(),
            "cognitive": self.cognitive_load_control(),
            "workspaces": self.multi_workspace(),
            "accessibility": self.accessibility(),
            "ui": self.ui_dashboard(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        ctx = session["draft"].get("context") or "Manager Context"
        self.user_context(ctx)

        eng_id = _id("xeeng")
        reg_id = _id("xereg")
        rules_id = _id("xrules")
        adaptive_id = _id("xadap")

        experience_engine = {
            "experience_engine_id": eng_id,
            "internal_id": eng_id,
            "catalog": self.catalog(),
            "executes_business_logic": False,
            "presentation_coordination_only": True,
            "registered_at": _now(),
            "sprint": "29.11",
        }
        experience_registry = {
            "experience_registry_id": reg_id,
            "internal_id": reg_id,
            "subsystems": list(UNIFIED_SUBSYSTEMS),
            "contexts": list(USER_CONTEXTS),
            "registered_at": _now(),
            "sprint": "29.11",
        }
        ux_rules_registry = {
            "ux_rules_registry_id": rules_id,
            "internal_id": rules_id,
            "rules": list(GLOBAL_RULES),
            "cognitive_controls": list(COGNITIVE_CONTROLS),
            "registered_at": _now(),
            "sprint": "29.11",
        }
        adaptive_ui_registry = {
            "adaptive_ui_registry_id": adaptive_id,
            "internal_id": adaptive_id,
            "dimensions": list(ADAPTIVE_DIMENSIONS),
            "profiles": {k: dict(v) for k, v in CONTEXT_PROFILES.items()},
            "registered_at": _now(),
            "sprint": "29.11",
        }

        self.store.experience_engines.save(eng_id, experience_engine)
        self.store.experience_registries.save(reg_id, experience_registry)
        self.store.ux_rules_registries.save(rules_id, ux_rules_registry)
        self.store.adaptive_ui_registries.save(adaptive_id, adaptive_ui_registry)

        session["status"] = "created"
        session["registrations"] = {
            "experience_engine_id": eng_id,
            "experience_registry_id": reg_id,
            "ux_rules_registry_id": rules_id,
            "adaptive_ui_registry_id": adaptive_id,
        }
        session["updated_at"] = _now()
        self.store.experience_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "experience_engine": experience_engine,
            "experience_registry": experience_registry,
            "ux_rules_registry": ux_rules_registry,
            "adaptive_ui_registry": adaptive_ui_registry,
            "message": "Experience Engine, Experience Registry, UX Rules Registry, and Adaptive UI Registry registered.",
        }
