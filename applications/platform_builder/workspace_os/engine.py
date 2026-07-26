"""Enterprise Workspace OS & Unified Workspace Platform — Sprint 29.12.

Workspace OS is the unified operating environment for every module.
Provides one consistent workspace while allowing every department,
AI team and application to have its own context.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.workspace_os.catalogs import (
    CONTEXT_LAYERS,
    INTEGRATED_MODULES,
    LAYOUT_FEATURES,
    LAYOUT_TEMPLATES,
    MULTITASKING_FEATURES,
    PERFORMANCE_FEATURES,
    SEARCH_SCOPES,
    SESSION_FEATURES,
    UI_SURFACES,
    WORKSPACE_OS_COMPONENTS,
    WORKSPACE_TYPES,
    WIZARD_STEPS,
    full_catalog,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class WorkspaceKernel:
    """Kernel for workspace lifecycle, layout, session, and context — OS layer only."""

    def __init__(self) -> None:
        self.active_workspace_type = "Manager Workspace"
        self.workspaces: list[dict[str, Any]] = [
            {
                "workspace_id": "wos_default",
                "name": "Primary Manager Workspace",
                "type": "Manager Workspace",
                "layout": dict(LAYOUT_TEMPLATES["Manager Workspace"]),
                "active": True,
                "tabs": ["AI Operations Center", "AI Team Map"],
                "pinned": ["AI Operations Center"],
            }
        ]
        self.active_workspace_id = "wos_default"
        self.session = {
            "session_id": "wos_session_default",
            "open_tabs": ["AI Operations Center", "AI Team Map"],
            "pinned_modules": ["AI Operations Center"],
            "active_context": {
                "Organization Context": "default_org",
                "Department Context": None,
                "Project Context": None,
                "Workflow Context": None,
                "AI Context": None,
                "User Context": "manager",
            },
            "recent_activity": [],
        }
        self.clipboard: list[dict[str, Any]] = []
        self.background_tasks: list[dict[str, Any]] = []
        self.cache: dict[str, Any] = {"enabled": True, "entries": 0}
        self.layout_state: dict[str, Any] = dict(LAYOUT_TEMPLATES["Manager Workspace"])

    def status(self) -> dict[str, Any]:
        return {
            "active_workspace_id": self.active_workspace_id,
            "active_workspace_type": self.active_workspace_type,
            "workspace_count": len(self.workspaces),
            "open_tabs": list(self.session["open_tabs"]),
            "pinned_modules": list(self.session["pinned_modules"]),
            "background_tasks": len(self.background_tasks),
            "clipboard_items": len(self.clipboard),
            "cache_enabled": self.cache["enabled"],
            "ready": True,
        }


class WorkspaceManager:
    """Manages workspace instances and switching."""

    def __init__(self, kernel: WorkspaceKernel) -> None:
        self.kernel = kernel

    def list_workspaces(self) -> list[dict[str, Any]]:
        return list(self.kernel.workspaces)

    def create(self, *, name: str | None = None, workspace_type: str | None = None) -> dict[str, Any]:
        wtype = workspace_type or "Manager Workspace"
        if wtype not in WORKSPACE_TYPES:
            raise ValidationError(f"Unsupported workspace type: {wtype}")
        wid = _id("wos")
        record = {
            "workspace_id": wid,
            "name": name or f"{wtype}",
            "type": wtype,
            "layout": dict(LAYOUT_TEMPLATES[wtype]),
            "active": False,
            "tabs": [],
            "pinned": [],
        }
        self.kernel.workspaces.append(record)
        return record

    def switch(self, workspace_id: str) -> dict[str, Any]:
        found = next((w for w in self.kernel.workspaces if w["workspace_id"] == workspace_id), None)
        if not found:
            raise NotFoundError(f"Workspace not found: {workspace_id}")
        for w in self.kernel.workspaces:
            w["active"] = w["workspace_id"] == workspace_id
        self.kernel.active_workspace_id = workspace_id
        self.kernel.active_workspace_type = found["type"]
        self.kernel.layout_state = dict(found["layout"])
        return found


class EnterpriseWorkspaceOS:
    """Enterprise Workspace OS — unified operating environment for platform modules."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.kernel = WorkspaceKernel()
        self.manager = WorkspaceManager(self.kernel)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.12",
            "workspace_os_ready": True,
            "workspace_manager_ready": True,
            "layout_engine_ready": True,
            "session_manager_ready": True,
            "context_engine_ready": True,
            "unified_workspace_platform_ready": True,
            "executes_business_logic": False,
            "unified_operating_environment": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.12",
            "executes_business_logic": False,
            "unified_operating_environment": True,
            "components": list(WORKSPACE_OS_COMPONENTS),
            "registered_os": len(self.store.workspace_os_instances.list_all()),
            "kernel": self.kernel.status(),
        }

    # Step 1 — Workspace OS Core
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Enterprise Workspace OS",
            "components": list(WORKSPACE_OS_COMPONENTS),
            "kernel": self.kernel.status(),
            "manager": {"workspace_count": len(self.manager.list_workspaces())},
            "executes_business_logic": False,
            "unified_operating_environment": True,
            "ready": True,
        }

    # Step 2 — Workspace Types
    def workspace_types(self, workspace_type: str | None = None) -> dict[str, Any]:
        if workspace_type:
            if workspace_type not in WORKSPACE_TYPES:
                raise ValidationError(f"Unsupported workspace type: {workspace_type}")
            self.kernel.active_workspace_type = workspace_type
            self.kernel.layout_state = dict(LAYOUT_TEMPLATES[workspace_type])
        return {
            "types": list(WORKSPACE_TYPES),
            "active_type": self.kernel.active_workspace_type,
            "templates": {k: dict(v) for k, v in LAYOUT_TEMPLATES.items()},
            "role_aware": True,
            "ready": True,
        }

    # Step 3 — Layout Engine
    def layout_engine(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            if "panels" in patch:
                self.kernel.layout_state["panels"] = list(patch["panels"])
            if "split" in patch:
                self.kernel.layout_state["split"] = patch["split"]
            if "template" in patch and patch["template"] in LAYOUT_TEMPLATES:
                self.kernel.layout_state = dict(LAYOUT_TEMPLATES[patch["template"]])
        return {
            "features": list(LAYOUT_FEATURES),
            "supported": {f: True for f in LAYOUT_FEATURES},
            "state": dict(self.kernel.layout_state),
            "templates": list(LAYOUT_TEMPLATES.keys()),
            "ready": True,
        }

    # Step 4 — Session Management
    def session_management(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            if "open_tabs" in patch and isinstance(patch["open_tabs"], list):
                self.kernel.session["open_tabs"] = list(patch["open_tabs"])
            if "pinned_modules" in patch and isinstance(patch["pinned_modules"], list):
                self.kernel.session["pinned_modules"] = list(patch["pinned_modules"])
            if "activity" in patch:
                self.kernel.session["recent_activity"].append(
                    {"at": _now(), "activity": patch["activity"]}
                )
            if patch.get("action") == "restore":
                self.kernel.session["restored_at"] = _now()
        return {
            "features": list(SESSION_FEATURES),
            "session": dict(self.kernel.session),
            "workspace_restore": True,
            "session_restore": True,
            "ready": True,
        }

    # Step 5 — Module Integration
    def module_integration(self, module: str | None = None) -> dict[str, Any]:
        if module:
            if module not in INTEGRATED_MODULES:
                raise ValidationError(f"Unsupported module: {module}")
            tabs = self.kernel.session["open_tabs"]
            if module not in tabs:
                tabs.append(module)
            self.kernel.session["recent_activity"].append(
                {"at": _now(), "activity": f"opened:{module}"}
            )
        return {
            "modules": list(INTEGRATED_MODULES),
            "integrated": {m: True for m in INTEGRATED_MODULES},
            "open_tabs": list(self.kernel.session["open_tabs"]),
            "ready": True,
        }

    # Step 6 — Context Engine
    def context_engine(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            for layer in CONTEXT_LAYERS:
                if layer in patch:
                    self.kernel.session["active_context"][layer] = patch[layer]
        return {
            "layers": list(CONTEXT_LAYERS),
            "active_context": dict(self.kernel.session["active_context"]),
            "maintained": {layer: True for layer in CONTEXT_LAYERS},
            "ready": True,
        }

    # Step 7 — Multitasking
    def multitasking(
        self,
        *,
        action: str | None = None,
        workspace_id: str | None = None,
        name: str | None = None,
        workspace_type: str | None = None,
        clipboard_item: dict[str, Any] | None = None,
        task: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if action == "create_workspace":
            self.manager.create(name=name, workspace_type=workspace_type)
        elif action == "switch":
            if not workspace_id:
                raise ValidationError("workspace_id is required to switch")
            self.manager.switch(workspace_id)
        elif action == "clipboard" and clipboard_item:
            self.kernel.clipboard.append({"at": _now(), **clipboard_item})
        elif action == "background_task" and task:
            self.kernel.background_tasks.append(
                {"task_id": _id("btask"), "at": _now(), **task, "status": "running"}
            )
        return {
            "features": list(MULTITASKING_FEATURES),
            "workspaces": self.manager.list_workspaces(),
            "active_workspace_id": self.kernel.active_workspace_id,
            "background_tasks": list(self.kernel.background_tasks),
            "clipboard": list(self.kernel.clipboard[-20:]),
            "live_synchronization": True,
            "cross_workspace_navigation": True,
            "ready": True,
        }

    # Step 8 — Workspace Search
    def workspace_search(self, query: str | None = None, scope: str | None = None) -> dict[str, Any]:
        scopes = list(SEARCH_SCOPES)
        if scope and scope not in SEARCH_SCOPES:
            raise ValidationError(f"Unsupported search scope: {scope}")
        results: list[dict[str, Any]] = []
        if query:
            q = query.lower()
            for m in INTEGRATED_MODULES:
                if q in m.lower():
                    results.append({"type": "module", "title": m, "scope": "Module Search"})
            for t in WORKSPACE_TYPES:
                if q in t.lower():
                    results.append({"type": "workspace_type", "title": t, "scope": "Global Search"})
            for cmd in ("switch workspace", "pin module", "restore session", "open layout editor"):
                if q in cmd:
                    results.append({"type": "command", "title": cmd, "scope": "Command Search"})
        return {
            "scopes": scopes,
            "query": query,
            "scope": scope or "Global Search",
            "results": results,
            "ready": True,
        }

    # Step 9 — Performance
    def performance(self, *, action: str | None = None) -> dict[str, Any]:
        if action == "cleanup":
            self.kernel.background_tasks = [
                t for t in self.kernel.background_tasks if t.get("status") == "running"
            ][:5]
            self.kernel.clipboard = self.kernel.clipboard[-10:]
            self.kernel.cache["entries"] = max(0, self.kernel.cache["entries"] - 1)
            self.kernel.cache["last_cleanup"] = _now()
        elif action == "warm_cache":
            self.kernel.cache["entries"] = self.kernel.cache.get("entries", 0) + 1
            self.kernel.cache["warmed_at"] = _now()
        return {
            "features": list(PERFORMANCE_FEATURES),
            "enabled": {f: True for f in PERFORMANCE_FEATURES},
            "cache": dict(self.kernel.cache),
            "lazy_module_loading": True,
            "memory_optimization": True,
            "ready": True,
        }

    # UI
    def ui_dashboard(self) -> dict[str, Any]:
        return {
            "surfaces": list(UI_SURFACES),
            "workspace_launcher": self.workspace_types(),
            "workspace_switcher": {
                "workspaces": self.manager.list_workspaces(),
                "active_workspace_id": self.kernel.active_workspace_id,
            },
            "context_bar": self.context_engine(),
            "session_manager": self.session_management(),
            "layout_editor": self.layout_engine(),
            "workspace_library": {
                "types": list(WORKSPACE_TYPES),
                "templates": {k: dict(v) for k, v in LAYOUT_TEMPLATES.items()},
            },
            "executes_business_logic": False,
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("wosz")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"workspace_type": "Manager Workspace"},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.workspace_os_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.workspace_os_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Workspace OS session not found: {session_id}")
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
        self.store.workspace_os_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Enterprise Workspace OS Summary",
            "core": self.engine_overview(),
            "types": self.workspace_types(),
            "layout": self.layout_engine(),
            "session": self.session_management(),
            "modules": self.module_integration(),
            "context": self.context_engine(),
            "multitasking": self.multitasking(),
            "search": self.workspace_search(),
            "performance": self.performance(),
            "ui": self.ui_dashboard(),
            "steps": WIZARD_STEPS,
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        wtype = session["draft"].get("workspace_type") or "Manager Workspace"
        self.workspace_types(wtype)

        os_id = _id("wosos")
        reg_id = _id("wosreg")
        layout_id = _id("woslay")
        ctx_id = _id("wosctx")
        sess_id = _id("wossm")

        workspace_os = {
            "workspace_os_id": os_id,
            "internal_id": os_id,
            "catalog": self.catalog(),
            "executes_business_logic": False,
            "unified_operating_environment": True,
            "registered_at": _now(),
            "sprint": "29.12",
        }
        workspace_registry = {
            "workspace_registry_id": reg_id,
            "internal_id": reg_id,
            "types": list(WORKSPACE_TYPES),
            "modules": list(INTEGRATED_MODULES),
            "registered_at": _now(),
            "sprint": "29.12",
        }
        layout_engine = {
            "layout_engine_id": layout_id,
            "internal_id": layout_id,
            "features": list(LAYOUT_FEATURES),
            "templates": {k: dict(v) for k, v in LAYOUT_TEMPLATES.items()},
            "registered_at": _now(),
            "sprint": "29.12",
        }
        context_engine = {
            "context_engine_id": ctx_id,
            "internal_id": ctx_id,
            "layers": list(CONTEXT_LAYERS),
            "registered_at": _now(),
            "sprint": "29.12",
        }
        session_manager = {
            "session_manager_id": sess_id,
            "internal_id": sess_id,
            "features": list(SESSION_FEATURES),
            "registered_at": _now(),
            "sprint": "29.12",
        }

        self.store.workspace_os_instances.save(os_id, workspace_os)
        self.store.workspace_registries.save(reg_id, workspace_registry)
        self.store.layout_engines.save(layout_id, layout_engine)
        self.store.context_engines.save(ctx_id, context_engine)
        self.store.session_managers.save(sess_id, session_manager)

        session["status"] = "created"
        session["registrations"] = {
            "workspace_os_id": os_id,
            "workspace_registry_id": reg_id,
            "layout_engine_id": layout_id,
            "context_engine_id": ctx_id,
            "session_manager_id": sess_id,
        }
        session["updated_at"] = _now()
        self.store.workspace_os_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "workspace_os": workspace_os,
            "workspace_registry": workspace_registry,
            "layout_engine": layout_engine,
            "context_engine": context_engine,
            "session_manager": session_manager,
            "message": (
                "Workspace OS, Workspace Registry, Layout Engine, "
                "Context Engine, and Session Manager registered."
            ),
        }
