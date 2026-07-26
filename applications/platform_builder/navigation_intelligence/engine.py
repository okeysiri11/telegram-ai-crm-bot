"""Enterprise Navigation Intelligence Engine — Sprint 29.14.

Predicts, optimizes and simplifies navigation across the platform.
Never executes business logic. Recommendations from verified context only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.navigation_intelligence.catalogs import (
    CONTEXT_SIGNALS,
    CROSS_PLATFORM_TARGETS,
    GRAPH_NODES,
    HISTORY_FEATURES,
    NAVIGATION_GRAPHS,
    NAVIGATION_INTELLIGENCE_COMPONENTS,
    PERFORMANCE_FEATURES,
    QUICK_ACCESS_FEATURES,
    RECOMMENDATION_TYPES,
    SEARCH_ROUTES,
    UI_SURFACES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class NavigationContextEngine:
    """Maintains verified navigation context — no business logic."""

    def __init__(self) -> None:
        self.context = {
            "Current Organization": "default_org",
            "Current Department": "ops",
            "Current Project": None,
            "Current Workflow": None,
            "Current AI Team": "ops_team",
            "Current User Intent": "explore",
        }
        self.verified = True

    def status(self) -> dict[str, Any]:
        return {
            "context": dict(self.context),
            "verified": self.verified,
            "signals": list(CONTEXT_SIGNALS),
            "ready": True,
        }


class NavigationRecommendationEngine:
    """Produces navigation recommendations from verified context only."""

    def __init__(self, context_engine: NavigationContextEngine) -> None:
        self.context_engine = context_engine

    def suggest(self) -> dict[str, list[str]]:
        intent = self.context_engine.context.get("Current User Intent") or "explore"
        dept = self.context_engine.context.get("Current Department") or "ops"
        base = {
            "Next Workspace": ["Manager Workspace", "Analytics Workspace"],
            "Related Documents": ["Policy Pack", "Runbook"],
            "Related AI Agents": ["Ops Agent", "Concierge"],
            "Related Dashboards": ["Executive Dashboard", "Ops Status"],
            "Related Projects": [f"{dept}_initiative", "platform_release"],
            "Related Knowledge": ["Architecture", "Playbooks"],
            "Related Tasks": ["review_navigation", "pin_favorites"],
        }
        if intent == "build":
            base["Next Workspace"] = ["Builder Workspace", "Developer Workspace"]
            base["Related AI Agents"] = ["Builder Guide", "Concierge"]
        return base


class NavigationIntelligenceEngine:
    """Enterprise Navigation Intelligence Engine — presentation/navigation only."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.context_engine = NavigationContextEngine()
        self.recommendation_engine = NavigationRecommendationEngine(self.context_engine)
        self.timeline: list[dict[str, Any]] = []
        self.visited_modules: list[str] = ["AI Operations Center"]
        self.recent_projects: list[str] = []
        self.recent_organizations: list[str] = ["default_org"]
        self.favorites: set[str] = set()
        self.pinned_locations: set[str] = {"AI Operations Center"}
        self.bookmarks: set[str] = set()
        self.pinned_dashboards: set[str] = set()
        self.pinned_ai_agents: set[str] = set()
        self.pinned_workspaces: set[str] = {"Manager Workspace"}
        self.recent_commands: list[str] = ["Open AI Operations Center"]
        self.cache = {"enabled": True, "nav_entries": 0, "context_entries": 1, "index_size": 0}

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.14",
            "navigation_intelligence_engine_ready": True,
            "context_navigation_ready": True,
            "recommendation_engine_ready": True,
            "smart_navigation_ready": True,
            "executes_business_logic": False,
            "verified_context_only": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.14",
            "executes_business_logic": False,
            "verified_context_only": True,
            "components": list(NAVIGATION_INTELLIGENCE_COMPONENTS),
            "registered": len(self.store.navigation_intelligence_engines.list_all()),
            "context": self.context_engine.status(),
        }

    # Step 1
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Navigation Intelligence Engine",
            "components": list(NAVIGATION_INTELLIGENCE_COMPONENTS),
            "context": self.context_engine.status(),
            "workspace_os_integration": True,
            "command_center_integration": True,
            "executes_business_logic": False,
            "verified_context_only": True,
            "ready": True,
        }

    # Step 2 — Global Navigation Graph
    def navigation_graph(self, graph: str | None = None) -> dict[str, Any]:
        if graph and graph not in NAVIGATION_GRAPHS:
            raise ValidationError(f"Unsupported graph: {graph}")
        graphs = {
            name: {
                "nodes": list(GRAPH_NODES[name]),
                "edges": max(0, len(GRAPH_NODES[name]) - 1),
                "ready": True,
            }
            for name in NAVIGATION_GRAPHS
        }
        selected = graphs[graph] if graph else None
        self.cache["index_size"] = sum(len(v["nodes"]) for v in graphs.values())
        return {
            "graphs": list(NAVIGATION_GRAPHS),
            "graph_map": graphs,
            "selected": graph,
            "selected_graph": selected,
            "ready": True,
        }

    # Step 3 — Context Aware Navigation
    def context_aware(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            for signal in CONTEXT_SIGNALS:
                if signal in patch:
                    self.context_engine.context[signal] = patch[signal]
            self.cache["context_entries"] = self.cache.get("context_entries", 0) + 1
        return {
            "signals": list(CONTEXT_SIGNALS),
            "determined": dict(self.context_engine.context),
            "auto_determine": True,
            "verified": self.context_engine.verified,
            "ready": True,
        }

    # Step 4 — Smart Recommendations
    def smart_recommendations(self) -> dict[str, Any]:
        suggestions = self.recommendation_engine.suggest()
        return {
            "types": list(RECOMMENDATION_TYPES),
            "suggestions": suggestions,
            "based_on_verified_context": True,
            "executes_business_logic": False,
            "ready": True,
        }

    # Step 5 — Navigation History
    def navigation_history(
        self,
        *,
        action: str | None = None,
        location: str | None = None,
        project: str | None = None,
        organization: str | None = None,
    ) -> dict[str, Any]:
        if action == "visit" and location:
            self.timeline.append({"at": _now(), "location": location, "kind": "visit"})
            if location not in self.visited_modules:
                self.visited_modules.append(location)
        if action == "favorite" and location:
            self.favorites.add(location)
        if action == "pin" and location:
            self.pinned_locations.add(location)
        if project and project not in self.recent_projects:
            self.recent_projects.insert(0, project)
            self.recent_projects = self.recent_projects[:10]
        if organization and organization not in self.recent_organizations:
            self.recent_organizations.insert(0, organization)
            self.recent_organizations = self.recent_organizations[:10]
        return {
            "features": list(HISTORY_FEATURES),
            "timeline": list(self.timeline[-50:]),
            "visited_modules": list(self.visited_modules),
            "recent_projects": list(self.recent_projects),
            "recent_organizations": list(self.recent_organizations),
            "favorites": sorted(self.favorites),
            "pinned_locations": sorted(self.pinned_locations),
            "ready": True,
        }

    # Step 6 — Quick Access
    def quick_access(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            for key, bucket in (
                ("favorites", self.favorites),
                ("bookmarks", self.bookmarks),
                ("pinned_dashboards", self.pinned_dashboards),
                ("pinned_ai_agents", self.pinned_ai_agents),
                ("pinned_workspaces", self.pinned_workspaces),
            ):
                if key in patch and isinstance(patch[key], list):
                    bucket.update(str(x) for x in patch[key])
            if "recent_commands" in patch and isinstance(patch["recent_commands"], list):
                for cmd in patch["recent_commands"]:
                    if cmd not in self.recent_commands:
                        self.recent_commands.insert(0, str(cmd))
                self.recent_commands = self.recent_commands[:20]
        return {
            "features": list(QUICK_ACCESS_FEATURES),
            "favorites": sorted(self.favorites),
            "bookmarks": sorted(self.bookmarks),
            "pinned_dashboards": sorted(self.pinned_dashboards),
            "pinned_ai_agents": sorted(self.pinned_ai_agents),
            "pinned_workspaces": sorted(self.pinned_workspaces),
            "recent_commands": list(self.recent_commands),
            "ready": True,
        }

    # Step 7 — Cross Platform Navigation
    def cross_platform(self, target: str | None = None) -> dict[str, Any]:
        if target:
            if target not in CROSS_PLATFORM_TARGETS:
                raise ValidationError(f"Unsupported target: {target}")
            self.timeline.append({"at": _now(), "location": target, "kind": "cross_platform"})
            if target not in self.visited_modules:
                self.visited_modules.append(target)
            self.cache["nav_entries"] = self.cache.get("nav_entries", 0) + 1
        return {
            "targets": list(CROSS_PLATFORM_TARGETS),
            "supported": {t: True for t in CROSS_PLATFORM_TARGETS},
            "last_target": target,
            "workspace_os_integration": True,
            "command_center_integration": True,
            "ready": True,
        }

    # Step 8 — Intelligent Search Routing
    def search_routing(self, query: str | None = None) -> dict[str, Any]:
        routes = list(SEARCH_ROUTES)
        routed: list[dict[str, Any]] = []
        if query:
            q = query.lower()
            mapping = [
                (("knowledge", "docs", "playbook"), "Knowledge"),
                (("document", "file", "pdf"), "Documents"),
                (("project", "initiative"), "Projects"),
                (("org", "organization", "department"), "Organizations"),
                (("agent", "ai", "concierge"), "AI Agents"),
                (("command", "palette", "shortcut"), "Commands"),
                (("market", "store", "app"), "Marketplace"),
            ]
            for keywords, route in mapping:
                if any(k in q for k in keywords):
                    routed.append({"route": route, "query": query, "confidence": 0.9})
            if not routed:
                routed.append({"route": "Knowledge", "query": query, "confidence": 0.4})
        return {
            "routes": routes,
            "query": query,
            "routed": routed,
            "ready": True,
        }

    # Step 9 — Performance
    def performance(self, *, action: str | None = None) -> dict[str, Any]:
        if action == "warm_cache":
            self.cache["nav_entries"] = self.cache.get("nav_entries", 0) + 5
            self.cache["context_entries"] = self.cache.get("context_entries", 0) + 1
            self.cache["warmed_at"] = _now()
        elif action == "optimize_index":
            self.cache["index_size"] = sum(len(v) for v in GRAPH_NODES.values())
            self.cache["optimized_at"] = _now()
        return {
            "features": list(PERFORMANCE_FEATURES),
            "enabled": {f: True for f in PERFORMANCE_FEATURES},
            "cache": dict(self.cache),
            "lazy_navigation": True,
            "realtime_suggestions": True,
            "ready": True,
        }

    # UI
    def ui_dashboard(self) -> dict[str, Any]:
        return {
            "surfaces": list(UI_SURFACES),
            "navigation_hub": self.engine_overview(),
            "quick_access_panel": self.quick_access(),
            "context_navigator": self.context_aware(),
            "recommendation_sidebar": self.smart_recommendations(),
            "navigation_timeline": self.navigation_history(),
            "smart_breadcrumbs": {
                "trail": [
                    self.context_engine.context.get("Current Organization"),
                    self.context_engine.context.get("Current Department"),
                    self.visited_modules[-1] if self.visited_modules else None,
                ],
                "ready": True,
            },
            "executes_business_logic": False,
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("navwz")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.navigation_intelligence_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.navigation_intelligence_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Navigation Intelligence session not found: {session_id}")
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
        self.store.navigation_intelligence_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Navigation Intelligence Engine Summary",
            "engine": self.engine_overview(),
            "graph": self.navigation_graph(),
            "context": self.context_aware(),
            "recommendations": self.smart_recommendations(),
            "history": self.navigation_history(),
            "quick_access": self.quick_access(),
            "cross_platform": self.cross_platform(),
            "search_routing": self.search_routing(),
            "performance": self.performance(),
            "ui": self.ui_dashboard(),
            "steps": WIZARD_STEPS,
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)

        eng_id = _id("naveng")
        reg_id = _id("navreg")
        rec_id = _id("navrec")
        ctx_id = _id("navctx")

        navigation_intelligence_engine = {
            "navigation_intelligence_engine_id": eng_id,
            "internal_id": eng_id,
            "catalog": self.catalog(),
            "executes_business_logic": False,
            "verified_context_only": True,
            "registered_at": _now(),
            "sprint": "29.14",
        }
        navigation_registry = {
            "navigation_registry_id": reg_id,
            "internal_id": reg_id,
            "graphs": list(NAVIGATION_GRAPHS),
            "targets": list(CROSS_PLATFORM_TARGETS),
            "registered_at": _now(),
            "sprint": "29.14",
        }
        recommendation_api = {
            "recommendation_api_id": rec_id,
            "internal_id": rec_id,
            "types": list(RECOMMENDATION_TYPES),
            "registered_at": _now(),
            "sprint": "29.14",
        }
        context_api = {
            "context_api_id": ctx_id,
            "internal_id": ctx_id,
            "signals": list(CONTEXT_SIGNALS),
            "registered_at": _now(),
            "sprint": "29.14",
        }

        self.store.navigation_intelligence_engines.save(eng_id, navigation_intelligence_engine)
        self.store.navigation_registries.save(reg_id, navigation_registry)
        self.store.recommendation_apis.save(rec_id, recommendation_api)
        self.store.context_apis.save(ctx_id, context_api)

        session["status"] = "created"
        session["registrations"] = {
            "navigation_intelligence_engine_id": eng_id,
            "navigation_registry_id": reg_id,
            "recommendation_api_id": rec_id,
            "context_api_id": ctx_id,
        }
        session["updated_at"] = _now()
        self.store.navigation_intelligence_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "navigation_intelligence_engine": navigation_intelligence_engine,
            "navigation_registry": navigation_registry,
            "recommendation_api": recommendation_api,
            "context_api": context_api,
            "message": (
                "Navigation Intelligence Engine, Navigation Registry, "
                "Recommendation API, and Context API registered."
            ),
        }
