"""Navigation library facade — Sprint 26.7."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_navigation.models import (
    API_PREFIX,
    ARCHITECTURE,
    COMMAND_KINDS,
    FAVORITE_KINDS,
    GLOBAL_NAV_SECTIONS,
    HISTORY_KINDS,
    HOTKEYS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    MENU_FEATURES,
    NAV_PATH,
    NAV_SURFACES,
    PERFORMANCE,
    PRINCIPLES,
    QUICK_SWITCH_TARGETS,
    SEARCH_CATEGORIES,
    SEARCH_MODES,
    SECURITY_GATES,
    VERSION,
    WORKSPACE_KINDS,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fuzzy(query: str, text: str) -> float:
    q = query.strip().lower()
    t = text.lower()
    if not q:
        return 0.0
    if q == t:
        return 1.0
    if q in t:
        return 0.85
    qi = 0
    for ch in t:
        if qi < len(q) and ch == q[qi]:
            qi += 1
    if qi == len(q):
        return 0.55
    qtok = set(re.findall(r"[a-z0-9]+", q))
    ttok = set(re.findall(r"[a-z0-9]+", t))
    if not qtok:
        return 0.0
    return len(qtok & ttok) / len(qtok) * 0.5


@dataclass
class _NavState:
    current_workspace: str = "personal"
    permissions: list[str] = field(default_factory=lambda: ["*"])
    organization: str = "demo_corp"
    tenant: str = "tenant_demo"
    page_times: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    paths: list[str] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)
    abandoned: int = 0


class NavigationLibrary:
    """Enterprise navigation: federation, registry, search, favorites, analytics."""

    def __init__(self) -> None:
        self._state = _NavState()
        self._workspaces = self._seed_workspaces()
        self._apps = self._seed_applications()
        self._nav = self._seed_global_nav()
        self._index = self._seed_search_index()
        self._favorites: list[dict[str, Any]] = [
            {"id": "fav_page_ws", "kind": "page", "label": "Workspace", "path": "/workspace"},
            {"id": "fav_dash", "kind": "dashboard", "label": "Executive Dashboard", "path": "/workspace/dashboards"},
            {"id": "fav_rep", "kind": "report", "label": "Weekly KPI", "path": "/workspace/reports/weekly"},
            {"id": "fav_cust", "kind": "customer", "label": "Acme Corp", "path": "/workspace/crm?client=acme"},
            {"id": "fav_prj", "kind": "project", "label": "Enterprise Web", "path": "/workspace/list"},
            {"id": "fav_cmd", "kind": "command", "label": "Open CRM", "path": "/workspace/crm"},
        ]
        self._history: list[dict[str, Any]] = []
        self._switch_cursor = 0

    def _seed_workspaces(self) -> list[dict[str, Any]]:
        return [
            {"id": "ws_personal", "kind": "personal", "name": "Personal Workspace", "route": "/workspace?scope=personal"},
            {"id": "ws_org", "kind": "organization", "name": "Organization Workspace", "route": "/workspace?scope=organization"},
            {"id": "ws_dept", "kind": "department", "name": "Department Workspace", "route": "/workspace?scope=department"},
            {"id": "ws_project", "kind": "project", "name": "Project Workspace", "route": "/workspace?scope=project"},
            {"id": "ws_customer", "kind": "customer", "name": "Customer Workspace", "route": "/workspace?scope=customer"},
            {"id": "ws_ai", "kind": "ai", "name": "AI Workspace", "route": "/workspace?scope=ai"},
            {"id": "ws_temp", "kind": "temporary", "name": "Temporary Workspace", "route": "/workspace?scope=temporary"},
        ]

    def _seed_applications(self) -> list[dict[str, Any]]:
        now = _now()
        apps = [
            ("auto_marketplace", "Auto Marketplace", "automotive", "4.2.0-enterprise"),
            ("agro_marketplace", "Agro Marketplace", "agro", "1.0"),
            ("agro_enterprise", "Agro Enterprise", "agro", "4.4.0-enterprise"),
            ("port_erp", "Port ERP", "port", "2.0.0"),
            ("port_enterprise", "Port Enterprise", "port", "4.6.0-enterprise"),
            ("drone_platform", "Drone Platform", "drone", "1.0"),
            ("crypto_enterprise", "Crypto Enterprise", "crypto", "4.8.0-enterprise"),
            ("legal_enterprise", "Legal Enterprise", "legal", "5.0.0-enterprise"),
            ("finance_enterprise", "Finance Enterprise", "finance", "5.2.0-enterprise"),
            ("enterprise_hub", "Enterprise Hub", "platform", "9.0.6"),
            ("marketplace", "AI Marketplace", "marketplace", "1.0"),
            ("workflow_studio", "Workflow Studio", "workflow", "1.0"),
            ("executive_center", "Executive Center", "analytics", "1.0"),
            ("ai_os", "AI OS", "ai", "3.4.0-alpha"),
            ("enterprise", "Enterprise Edition", "platform", "4.0.0-enterprise"),
            ("command_center", "Command Center", "productivity", "9.0.6"),
        ]
        out = []
        for code, name, owner, version in apps:
            out.append(
                {
                    "id": f"app_{code}",
                    "code": code,
                    "icon": code[:2].upper(),
                    "name": name,
                    "status": "healthy",
                    "owner": owner,
                    "permissions": ["read", "navigate"],
                    "version": version,
                    "health": "ok",
                    "last_update": now,
                    "route": f"/workspace/{code.replace('_', '-')}",
                }
            )
        return out

    def _seed_global_nav(self) -> list[dict[str, Any]]:
        mapping = {
            "applications": "/workspace",
            "verticals": "/workspace/auto",
            "crm": "/workspace/crm",
            "erp": "/workspace/erp",
            "finance": "/workspace/finance",
            "analytics": "/workspace/analytics",
            "marketplace": "/workspace/marketplace",
            "knowledge": "/workspace/docs/security",
            "ai_studio": "/workspace/ai",
            "dashboards": "/workspace/dashboards",
            "reports": "/workspace/reports/weekly",
            "settings": "/settings",
            "automations": "/workspace?action=automations",
            "workflows": "/workspace/workflows/invoice",
            "documents": "/workspace/docs/security",
        }
        return [
            {"id": f"nav_{s}", "section": s, "label": s.replace("_", " ").title(), "route": mapping[s]}
            for s in GLOBAL_NAV_SECTIONS
        ]

    def _seed_search_index(self) -> list[dict[str, Any]]:
        rows = [
            ("crm", "Client Acme Corp", "/workspace/crm?client=acme", ["client", "acme"]),
            ("erp", "SKU-1042 Brake Pad", "/workspace/erp?sku=1042", ["sku", "inventory"]),
            ("knowledge", "Security Policy", "/workspace/docs/security", ["security", "policy"]),
            ("reports", "Weekly KPI", "/workspace/reports/weekly", ["report", "kpi"]),
            ("users", "Alex Owner", "/identity/users", ["user", "alex"]),
            ("organizations", "Demo Corp", "/identity/organizations", ["org", "demo"]),
            ("projects", "Enterprise Web", "/workspace/list", ["project", "web"]),
            ("tasks", "Review Migration", "/workspace?task=migration", ["task"]),
            ("documents", "Q3 Brief", "/workspace/docs/q3", ["document", "brief"]),
            ("marketplace", "Extension Catalog", "/workspace/marketplace", ["marketplace"]),
            ("ai_agents", "Ops Copilot", "/workspace/ai", ["agent", "copilot"]),
            ("applications", "Enterprise Hub", "/workspace", ["hub", "enterprise"]),
            ("dashboards", "Personal Dashboard", "/workspace/dashboards", ["dashboard"]),
            ("widgets", "Recent Activity Widget", "/command-center#recent_activity", ["widget"]),
            ("workflows", "Invoice Approval", "/workspace/workflows/invoice", ["workflow"]),
            ("finance", "Treasury Summary", "/workspace/finance", ["finance", "treasury"]),
            ("modules", "CRM Module", "/workspace/crm", ["crm", "module"]),
        ]
        return [
            {
                "id": f"idx_{cat}_{i}",
                "category": cat,
                "title": title,
                "path": path,
                "tokens": tokens,
            }
            for i, (cat, title, path, tokens) in enumerate(rows)
        ]

    # —— public ——
    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def inventory(self) -> dict[str, Any]:
        return {
            "architecture": list(ARCHITECTURE),
            "surfaces": list(NAV_SURFACES),
            "global_nav_sections": list(GLOBAL_NAV_SECTIONS),
            "workspace_kinds": list(WORKSPACE_KINDS),
            "menu_features": list(MENU_FEATURES),
            "command_kinds": list(COMMAND_KINDS),
            "search_categories": list(SEARCH_CATEGORIES),
            "search_modes": list(SEARCH_MODES),
            "performance": list(PERFORMANCE),
            "hotkeys": list(HOTKEYS),
            "favorite_kinds": list(FAVORITE_KINDS),
            "history_kinds": list(HISTORY_KINDS),
            "quick_switch_targets": list(QUICK_SWITCH_TARGETS),
            "security_gates": list(SECURITY_GATES),
            "path": NAV_PATH,
            "api_prefix": API_PREFIX,
            "architecture_count": len(ARCHITECTURE),
            "search_category_count": len(SEARCH_CATEGORIES),
            "global_nav_count": len(GLOBAL_NAV_SECTIONS),
            "workspace_kind_count": len(WORKSPACE_KINDS),
            "application_count": len(self._apps),
            "passed": True,
        }

    def global_navigation(self, *, permissions: list[str] | None = None) -> dict[str, Any]:
        perms = set(permissions if permissions is not None else self._state.permissions)
        items = []
        for item in self._nav:
            if self._allowed(item["section"], perms):
                items.append(item)
        return {"sections": list(GLOBAL_NAV_SECTIONS), "items": items, "count": len(items)}

    def _allowed(self, resource: str, perms: set[str]) -> bool:
        if "*" in perms:
            return True
        if not perms:
            return False
        return resource in perms or resource.split("_")[0] in perms or "navigate" in perms

    def workspaces(self) -> dict[str, Any]:
        return {
            "kinds": list(WORKSPACE_KINDS),
            "workspaces": self._workspaces,
            "current": self._state.current_workspace,
        }

    def switch_workspace(self, kind_or_id: str, *, permissions: list[str] | None = None) -> dict[str, Any]:
        if permissions is not None and len(permissions) == 0:
            return {"ok": False, "error": "permission_denied", "gates": list(SECURITY_GATES)}
        perms = set(permissions if permissions is not None else self._state.permissions)
        if not self._allowed("workspace", perms) and "*" not in perms:
            return {"ok": False, "error": "permission_denied", "gates": list(SECURITY_GATES)}
        ws = next(
            (w for w in self._workspaces if w["kind"] == kind_or_id or w["id"] == kind_or_id),
            None,
        )
        if ws is None:
            return {"ok": False, "error": "workspace_not_found"}
        self._state.current_workspace = ws["kind"]
        self.track_history("page", ws["name"], ws["route"])
        return {
            "ok": True,
            "workspace": ws,
            "isolation": {
                "workspace": ws["kind"],
                "tenant": self._state.tenant,
                "organization": self._state.organization,
            },
            "gates": list(SECURITY_GATES),
        }

    def application_registry(self) -> dict[str, Any]:
        return {
            "applications": self._apps,
            "count": len(self._apps),
            "auto_registered": True,
        }

    def search(self, query: str, *, limit: int = 20, permissions: list[str] | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        perms = set(permissions if permissions is not None else self._state.permissions)
        results = []
        for doc in self._index:
            if not self._allowed(doc["category"], perms) and "*" not in perms:
                if permissions is not None and len(permissions) == 0:
                    continue
                if permissions is not None and "*" not in perms and doc["category"] not in perms:
                    continue
            hay = " ".join([doc["title"], doc["category"], *doc["tokens"]])
            score = _fuzzy(query, hay) if query.strip() else 0.4
            if query.strip() and score < 0.25:
                continue
            results.append({**doc, "score": round(score, 4), "match": "fuzzy" if query.strip() else "exact"})
        results.sort(key=lambda r: r["score"], reverse=True)
        elapsed = (time.perf_counter() - t0) * 1000
        record = {"query": query, "hits": len(results), "at": _now(), "elapsed_ms": round(elapsed, 3)}
        self._state.searches.append(record)
        if query.strip() and not results:
            self._state.abandoned += 1
        if query.strip():
            self.track_history("search", query, None)
        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
            "elapsed_ms": round(elapsed, 3),
            "categories": list(SEARCH_CATEGORIES),
            "fuzzy": True,
        }

    def favorites(self) -> dict[str, Any]:
        return {"kinds": list(FAVORITE_KINDS), "items": list(self._favorites), "count": len(self._favorites)}

    def add_favorite(self, entry: dict[str, Any]) -> dict[str, Any]:
        eid = entry.get("id") or f"fav_{int(time.time() * 1000)}"
        item = {
            "id": eid,
            "kind": entry.get("kind", "page"),
            "label": entry.get("label", eid),
            "path": entry.get("path", "/workspace"),
        }
        self._favorites = [item] + [f for f in self._favorites if f["id"] != eid]
        return self.favorites()

    def track_history(self, kind: str, label: str, path: str | None) -> dict[str, Any]:
        item = {"id": f"h_{len(self._history)+1}_{int(time.time()*1000)%100000}", "kind": kind, "label": label, "path": path, "at": _now()}
        self._history = [item] + self._history
        self._history = self._history[:100]
        if path:
            self._state.paths.append(path)
            self._state.paths = self._state.paths[-200:]
        return item

    def history(self, kind: str | None = None) -> dict[str, Any]:
        items = [h for h in self._history if kind is None or h["kind"] == kind]
        grouped = {k: [h for h in self._history if h["kind"] == k][:8] for k in HISTORY_KINDS}
        return {"kinds": list(HISTORY_KINDS), "items": items[:50], "grouped": grouped, "count": len(items)}

    def breadcrumbs(self, pathname: str) -> dict[str, Any]:
        parts = [p for p in pathname.split("/") if p]
        crumbs = [{"label": "Workspace", "path": "/workspace", "level": "workspace"}]
        acc = ""
        levels = ("module", "section", "page", "entity")
        for i, part in enumerate(parts):
            acc += f"/{part}"
            crumbs.append(
                {
                    "label": part.replace("-", " ").replace("_", " "),
                    "path": acc,
                    "level": levels[min(i, len(levels) - 1)],
                }
            )
        return {"path": pathname, "crumbs": crumbs, "depth": len(crumbs)}

    def quick_switcher(self, *, step: int = 1, target: str | None = None) -> dict[str, Any]:
        pools: dict[str, list[dict[str, Any]]] = {
            "applications": [{"id": a["id"], "label": a["name"], "route": a["route"]} for a in self._apps[:8]],
            "dashboards": [{"id": "dash_main", "label": "Personal Dashboard", "route": "/workspace/dashboards"}],
            "workspaces": [{"id": w["id"], "label": w["name"], "route": w["route"]} for w in self._workspaces],
            "ai_chats": [{"id": "ai_ops", "label": "Ops Copilot", "route": "/workspace/ai"}],
            "documents": [{"id": "doc_sec", "label": "Security Policy", "route": "/workspace/docs/security"}],
        }
        target_key = target if target in pools else "applications"
        items = pools[target_key]
        if not items:
            return {"ok": False, "error": "empty_pool"}
        self._switch_cursor = (self._switch_cursor + step) % len(items)
        selected = items[self._switch_cursor]
        self.track_history("page", selected["label"], selected["route"])
        return {
            "ok": True,
            "target": target_key,
            "targets": list(QUICK_SWITCH_TARGETS),
            "selected": selected,
            "items": items,
            "hotkey": "Ctrl+Tab",
        }

    def analytics(self) -> dict[str, Any]:
        popular: dict[str, int] = defaultdict(int)
        for p in self._state.paths:
            popular[p] += 1
        search_stats = {
            "total": len(self._state.searches),
            "abandoned": self._state.abandoned,
            "avg_hits": round(
                sum(s["hits"] for s in self._state.searches) / max(len(self._state.searches), 1),
                2,
            ),
        }
        return {
            "navigation_paths": self._state.paths[-50:],
            "popular_pages": sorted(
                ({"path": k, "count": v} for k, v in popular.items()),
                key=lambda x: x["count"],
                reverse=True,
            )[:15],
            "search_statistics": search_stats,
            "abandoned_searches": self._state.abandoned,
            "time_per_page": {k: round(sum(v) / len(v), 3) if v else 0.0 for k, v in self._state.page_times.items()},
            "ai_recommendations": [
                "pin_top_crm_pages",
                "enable_workspace_prefetch",
                "review_abandoned_searches",
            ],
            "dashboard_ready": True,
        }

    def record_page_time(self, path: str, ms: float) -> None:
        self._state.page_times[path].append(ms)

    def validate_permissions(self, resource: str, permissions: list[str]) -> dict[str, Any]:
        ok = self._allowed(resource, set(permissions))
        if not permissions:
            ok = False
        return {
            "resource": resource,
            "allowed": ok,
            "gates": list(SECURITY_GATES),
            "permissions": permissions,
            "workspace": self._state.current_workspace,
            "tenant": self._state.tenant,
            "organization": self._state.organization,
        }

    def dashboard(self) -> dict[str, Any]:
        inv = self.inventory()
        return {
            "navigation_ready": True,
            "command_palette_ready": True,
            "global_search_ready": True,
            "menu_engine_ready": True,
            "search_index_ready": True,
            "shortcuts_ready": True,
            "workspace_federation_ready": True,
            "application_registry_ready": True,
            "smart_favorites_ready": True,
            "recent_history_ready": True,
            "enterprise_breadcrumbs_ready": True,
            "quick_switcher_ready": True,
            "navigation_analytics_ready": True,
            "path": NAV_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
            "search_category_count": inv["search_category_count"],
            "hotkeys": inv["hotkeys"],
            "current_workspace": self._state.current_workspace,
            "application_count": inv["application_count"],
            "analytics": self.analytics(),
            "kpi": dict(KPI_TARGETS),
            "recommendations": ["connect_semantic_search_backend", "enable_route_prefetch_in_router"],
        }

    def integrations(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_workspace_search": False,
            "palette_hotkeys": list(HOTKEYS),
            "federation": True,
            "registry": True,
        }

    def bootstrap(self) -> dict[str, Any]:
        inv = self.inventory()
        dash = self.dashboard()
        links = self.integrations()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "navigation_ready": True,
            "command_palette_ready": True,
            "global_search_ready": True,
            "menu_engine_ready": True,
            "search_index_ready": True,
            "favorites_ready": True,
            "history_ready": True,
            "shortcuts_ready": True,
            "breadcrumbs_ready": True,
            "performance_ready": True,
            "workspace_federation_ready": True,
            "application_registry_ready": True,
            "smart_favorites_ready": True,
            "recent_history_ready": True,
            "enterprise_breadcrumbs_ready": True,
            "quick_switcher_ready": True,
            "navigation_analytics_ready": True,
            "path": NAV_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
            "kpi": dict(KPI_TARGETS),
            "status": "ready",
            "integrations": links,
            "full": {
                "inventory": inv,
                "dashboard": dash,
                "links": links,
                "global_nav": self.global_navigation(),
                "workspaces": self.workspaces(),
                "registry": self.application_registry(),
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": list(ARCHITECTURE),
            "principles": self.principles(),
            "path": NAV_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
            "current_workspace": self._state.current_workspace,
        }


navigation_library = NavigationLibrary()
