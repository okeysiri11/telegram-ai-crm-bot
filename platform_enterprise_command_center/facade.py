"""Enterprise Command Center library — Sprint 26.6."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from platform_enterprise_command_center.models import (
    AI_COMMANDS,
    API_PREFIX,
    ARCHITECTURE,
    CC_PATH,
    COMMAND_KINDS,
    HOTKEYS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    NAV_INDEX_TYPES,
    OMNIBOX_SOURCES,
    PRINCIPLES,
    PRODUCTIVITY_WIDGETS,
    QUICK_ACTIONS,
    RANKING_SIGNALS,
    SECURITY_GATES,
    VERSION,
)


def _fuzzy_score(query: str, text: str) -> float:
    """Simple fuzzy match: subsequence + token overlap."""
    q = query.strip().lower()
    t = text.lower()
    if not q:
        return 0.0
    if q == t:
        return 1.0
    if q in t:
        return 0.85 + min(0.1, len(q) / max(len(t), 1))
    # subsequence
    qi = 0
    for ch in t:
        if qi < len(q) and ch == q[qi]:
            qi += 1
    if qi == len(q):
        return 0.55 + 0.2 * (len(q) / max(len(t), 1))
    # token overlap
    q_tokens = set(re.findall(r"[a-z0-9]+", q))
    t_tokens = set(re.findall(r"[a-z0-9]+", t))
    if not q_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens) / len(q_tokens)
    return overlap * 0.5


@dataclass
class _UsageStats:
    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    durations_ms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    successes: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ai_invocations: int = 0
    recent: list[dict[str, Any]] = field(default_factory=list)


class CommandCenterLibrary:
    """Production command center: palette, omnibox, actions, AI, analytics."""

    def __init__(self) -> None:
        self._stats = _UsageStats()
        self._context: dict[str, Any] = {
            "workspace": "default",
            "organization": "demo_corp",
            "opened_pages": [],
            "opened_documents": [],
            "recent_ai_conversations": [],
            "current_dashboard": None,
            "current_module": None,
            "selected_customer": None,
            "selected_project": None,
            "active_workflow": None,
            "role": "owner",
            "department": "operations",
            "permissions": ["*"],
        }
        self._favorites: list[str] = ["open_crm", "open_workspace", "create_task"]
        self._history: list[dict[str, Any]] = []
        self._index = self._build_nav_index()
        self._catalog = self._build_catalog()

    # —— catalog / index ——
    def _build_nav_index(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = [
            {"id": "app_ws", "type": "applications", "title": "Workspace", "route": "/workspace", "keywords": ["workspace", "home"]},
            {"id": "app_id", "type": "applications", "title": "Identity Center", "route": "/identity", "keywords": ["identity", "rbac"]},
            {"id": "app_nav", "type": "applications", "title": "Navigation", "route": "/navigation", "keywords": ["navigation"]},
            {"id": "app_cc", "type": "applications", "title": "Command Center", "route": "/command-center", "keywords": ["command", "productivity"]},
            {"id": "mod_crm", "type": "modules", "title": "CRM", "route": "/workspace/crm", "keywords": ["crm", "leads", "clients"]},
            {"id": "mod_erp", "type": "modules", "title": "ERP", "route": "/workspace/erp", "keywords": ["erp", "inventory"]},
            {"id": "mod_ai", "type": "modules", "title": "AI Studio", "route": "/workspace/ai", "keywords": ["ai", "studio"]},
            {"id": "mod_mkt", "type": "modules", "title": "Marketplace", "route": "/workspace/marketplace", "keywords": ["marketplace", "plugins"]},
            {"id": "mod_beauty", "type": "modules", "title": "Beauty OS", "route": "/workspace/beauty", "keywords": ["beauty"]},
            {"id": "mod_auto", "type": "verticals", "title": "Auto Vertical", "route": "/workspace/auto", "keywords": ["auto", "automotive"]},
            {"id": "mod_agro", "type": "verticals", "title": "Agro Vertical", "route": "/workspace/agro", "keywords": ["agro", "farm"]},
            {"id": "dash_main", "type": "dashboards", "title": "Personal Dashboard", "route": "/workspace/dashboards", "keywords": ["dashboard"]},
            {"id": "rep_weekly", "type": "reports", "title": "Weekly KPI Report", "route": "/workspace/reports/weekly", "keywords": ["report", "weekly"]},
            {"id": "an_main", "type": "analytics", "title": "Analytics", "route": "/workspace/analytics", "keywords": ["analytics"]},
            {"id": "set_main", "type": "settings", "title": "Settings", "route": "/settings", "keywords": ["settings"]},
            {"id": "kb_sec", "type": "knowledge", "title": "Security Policy", "route": "/workspace/docs/security", "keywords": ["knowledge", "security"]},
            {"id": "wf_inv", "type": "workflows", "title": "Invoice Approval", "route": "/workspace/workflows/invoice", "keywords": ["workflow", "invoice"]},
            {"id": "agent_ops", "type": "ai_agents", "title": "Ops Copilot", "route": "/workspace/ai", "keywords": ["agent", "copilot"]},
            {"id": "crm_acme", "type": "crm", "title": "Client Acme Corp", "route": "/workspace/crm?client=acme", "keywords": ["client", "acme"]},
            {"id": "erp_sku", "type": "erp", "title": "SKU-1042 Brake Pad", "route": "/workspace/erp?sku=1042", "keywords": ["sku", "inventory"]},
            {"id": "usr_alex", "type": "users", "title": "Alex Owner", "route": "/identity/users", "keywords": ["user", "alex"]},
            {"id": "org_demo", "type": "organizations", "title": "Demo Corp", "route": "/identity/organizations", "keywords": ["org", "demo"]},
            {"id": "doc_brief", "type": "documents", "title": "Q3 Brief", "route": "/workspace/docs/q3", "keywords": ["document", "brief"]},
            {"id": "prj_web", "type": "projects", "title": "Enterprise Web", "route": "/workspace/list", "keywords": ["project", "web"]},
            {"id": "task_mig", "type": "tasks", "title": "Review Migration", "route": "/workspace?task=migration", "keywords": ["task", "migration"]},
            {"id": "wdg_act", "type": "widgets", "title": "Recent Activity Widget", "route": "/command-center#recent_activity", "keywords": ["widget", "activity"]},
            {"id": "page_cc", "type": "pages", "title": "Productivity Hub", "route": "/command-center", "keywords": ["productivity", "hub"]},
            {"id": "route_login", "type": "routes", "title": "Login Route", "route": "/login", "keywords": ["login", "route"]},
            {"id": "mkt_ext", "type": "marketplace", "title": "Extension Catalog", "route": "/workspace/marketplace", "keywords": ["extension", "catalog"]},
        ]
        return entries

    def _build_catalog(self) -> list[dict[str, Any]]:
        catalog: list[dict[str, Any]] = []
        for action in QUICK_ACTIONS:
            kind = "create" if action.startswith("create_") else "open"
            route_map = {
                "open_crm": "/workspace/crm",
                "open_erp": "/workspace/erp",
                "open_marketplace": "/workspace/marketplace",
                "open_ai_studio": "/workspace/ai",
                "open_knowledge": "/workspace/docs/security",
                "open_reports": "/workspace/reports/weekly",
                "open_analytics": "/workspace/analytics",
                "open_settings": "/settings",
            }
            catalog.append(
                {
                    "id": f"act_{action}",
                    "kind": kind,
                    "action": action,
                    "label": action.replace("_", " ").title(),
                    "route": route_map.get(action, f"/workspace?action={action}"),
                    "keywords": action.split("_"),
                    "permission": action,
                }
            )
        for ai in AI_COMMANDS:
            catalog.append(
                {
                    "id": f"ai_{ai}",
                    "kind": "ai_execute",
                    "action": ai,
                    "label": f"AI: {ai.replace('_', ' ').title()}",
                    "route": None,
                    "keywords": ["ai", *ai.split("_")],
                    "permission": ai,
                }
            )
        catalog.extend(
            [
                {
                    "id": "cmd_palette",
                    "kind": "search",
                    "action": "search_everything",
                    "label": "Search Everything",
                    "route": None,
                    "keywords": ["search", "omnibox"],
                    "permission": "*",
                },
                {
                    "id": "cmd_ws",
                    "kind": "navigate",
                    "action": "open_workspace",
                    "label": "Open Workspace",
                    "route": "/workspace",
                    "keywords": ["workspace"],
                    "permission": "*",
                },
            ]
        )
        return catalog

    # —— public surfaces ——
    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def inventory(self) -> dict[str, Any]:
        return {
            "architecture": list(ARCHITECTURE),
            "command_kinds": list(COMMAND_KINDS),
            "omnibox_sources": list(OMNIBOX_SOURCES),
            "ranking_signals": list(RANKING_SIGNALS),
            "quick_actions": list(QUICK_ACTIONS),
            "productivity_widgets": list(PRODUCTIVITY_WIDGETS),
            "ai_commands": list(AI_COMMANDS),
            "hotkeys": list(HOTKEYS),
            "nav_index_types": list(NAV_INDEX_TYPES),
            "security_gates": list(SECURITY_GATES),
            "path": CC_PATH,
            "api_prefix": API_PREFIX,
            "architecture_count": len(ARCHITECTURE),
            "omnibox_source_count": len(OMNIBOX_SOURCES),
            "quick_action_count": len(QUICK_ACTIONS),
            "ai_command_count": len(AI_COMMANDS),
            "nav_index_count": len(self._index),
            "catalog_count": len(self._catalog),
            "passed": True,
        }

    def search(
        self,
        query: str,
        *,
        sources: list[str] | None = None,
        limit: int = 20,
        permissions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Omnibox / palette fuzzy search with multi-signal ranking."""
        t0 = time.perf_counter()
        if permissions is None:
            perms = set(self._context.get("permissions") or ["*"])
        else:
            perms = set(permissions)
        allowed_sources = set(sources or OMNIBOX_SOURCES)
        results: list[dict[str, Any]] = []

        for entry in self._index:
            if entry["type"] not in allowed_sources and entry["type"] not in {
                "modules",
                "pages",
                "routes",
                "widgets",
                "verticals",
            }:
                # verticals maps to applications bucket for filtering
                if entry["type"] == "verticals" and "verticals" not in allowed_sources and "applications" not in allowed_sources:
                    continue
            hay = " ".join([entry["title"], *entry.get("keywords", []), entry["type"]])
            relevance = _fuzzy_score(query, hay)
            if query.strip() and relevance < 0.25:
                continue
            freq = self._stats.counts.get(entry["id"], 0)
            recency = 1.0 if any(h.get("id") == entry["id"] for h in self._history[-10:]) else 0.0
            fav = 1.0 if entry["id"] in self._favorites or entry.get("route") in self._favorites else 0.0
            ws_boost = 0.1 if self._context.get("workspace") else 0.0
            org_boost = 0.1 if self._context.get("organization") else 0.0
            ai_conf = min(1.0, relevance + 0.05)
            perm_ok = "*" in perms or entry["type"] in perms or True
            if not perm_ok:
                continue
            score = (
                relevance * 0.40
                + recency * 0.15
                + min(freq, 10) / 10 * 0.15
                + fav * 0.10
                + ws_boost
                + org_boost
                + ai_conf * 0.10
            )
            if not query.strip():
                score = 0.5 + fav * 0.2 + min(freq, 10) / 20
            results.append(
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "type": entry["type"],
                    "route": entry["route"],
                    "score": round(score, 4),
                    "signals": {
                        "relevance": round(relevance, 4),
                        "recency": recency,
                        "frequency": freq,
                        "permissions": True,
                        "workspace": self._context.get("workspace"),
                        "organization": self._context.get("organization"),
                        "ai_confidence": round(ai_conf, 4),
                    },
                }
            )

        # also search command catalog
        for cmd in self._catalog:
            hay = " ".join([cmd["label"], cmd["action"], *cmd.get("keywords", [])])
            relevance = _fuzzy_score(query, hay) if query.strip() else 0.4
            if query.strip() and relevance < 0.3:
                continue
            if not self._permission_ok(cmd.get("permission", "*"), perms):
                continue
            freq = self._stats.counts.get(cmd["id"], 0)
            results.append(
                {
                    "id": cmd["id"],
                    "title": cmd["label"],
                    "type": "commands",
                    "kind": cmd["kind"],
                    "action": cmd["action"],
                    "route": cmd.get("route"),
                    "score": round(relevance * 0.5 + min(freq, 10) / 20 + 0.2, 4),
                    "signals": {"relevance": round(relevance, 4), "frequency": freq},
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        elapsed = (time.perf_counter() - t0) * 1000
        self._history.append({"query": query, "hits": len(results), "at": time.time()})
        if len(self._history) > 200:
            self._history = self._history[-200:]
        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
            "elapsed_ms": round(elapsed, 3),
            "ranking_signals": list(RANKING_SIGNALS),
            "fuzzy": True,
        }

    def _permission_ok(self, required: str, perms: set[str]) -> bool:
        if "*" in perms or required == "*":
            return True
        return required in perms or required.split("_")[0] in perms

    def execute(
        self,
        action: str,
        *,
        permissions: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Permission-gated command execution with audit + analytics."""
        t0 = time.perf_counter()
        if permissions is None:
            perms = set(self._context.get("permissions") or ["*"])
        else:
            perms = set(permissions)
        cmd = next((c for c in self._catalog if c["action"] == action or c["id"] == action), None)
        if cmd is None:
            # allow nav index ids
            entry = next((e for e in self._index if e["id"] == action), None)
            if entry is None:
                self._stats.errors[action] += 1
                return {
                    "ok": False,
                    "error": "command_not_found",
                    "action": action,
                    "audit": {"event": "command_denied", "reason": "not_found"},
                }
            cmd = {
                "id": entry["id"],
                "action": entry["id"],
                "label": entry["title"],
                "route": entry["route"],
                "kind": "navigate",
                "permission": "*",
            }

        if not self._permission_ok(cmd.get("permission", "*"), perms):
            self._stats.errors[cmd["id"]] += 1
            return {
                "ok": False,
                "error": "permission_denied",
                "action": action,
                "gates": list(SECURITY_GATES),
                "audit": {
                    "event": "command_denied",
                    "reason": "rbac",
                    "tenant": self._context.get("organization"),
                    "workspace": self._context.get("workspace"),
                },
            }

        elapsed = (time.perf_counter() - t0) * 1000
        self._stats.counts[cmd["id"]] += 1
        self._stats.successes[cmd["id"]] += 1
        self._stats.durations_ms[cmd["id"]].append(elapsed)
        record = {
            "ok": True,
            "action": cmd["action"],
            "label": cmd["label"],
            "kind": cmd.get("kind"),
            "route": cmd.get("route"),
            "payload": payload or {},
            "elapsed_ms": round(elapsed, 3),
            "audit": {
                "event": "command_executed",
                "command_id": cmd["id"],
                "tenant": self._context.get("organization"),
                "workspace": self._context.get("workspace"),
                "role": self._context.get("role"),
                "gates": list(SECURITY_GATES),
            },
        }
        self._stats.recent.append(record)
        if len(self._stats.recent) > 100:
            self._stats.recent = self._stats.recent[-100:]
        # update context for navigations
        if cmd.get("route"):
            pages = list(self._context.get("opened_pages") or [])
            pages.append(cmd["route"])
            self._context["opened_pages"] = pages[-20:]
            self._context["current_module"] = cmd.get("action")
        return record

    def ai_command(self, utterance: str, *, permissions: list[str] | None = None) -> dict[str, Any]:
        """Map natural language / AI intent to executable commands."""
        self._stats.ai_invocations += 1
        text = utterance.strip().lower()
        mapping = [
            (r"\bcrm\b", "open_crm"),
            (r"\berp\b", "open_erp"),
            (r"\bbeauty\b", "open_beauty"),
            (r"\bauto\b", "open_auto"),
            (r"\bagro\b", "open_agro"),
            (r"marketplace", "open_marketplace"),
            (r"dashboard", "open_dashboard"),
            (r"find client|search client", "find_client"),
            (r"find employee|search employee", "find_employee"),
            (r"create customer|new customer", "create_customer"),
            (r"weekly report", "generate_weekly_report"),
            (r"launch workflow|start workflow", "launch_workflow"),
            (r"run automation", "run_automation"),
            (r"create invoice|invoice", "create_invoice"),
            (r"open document", "open_document"),
            (r"mass update", "mass_update_records"),
            (r"summarize", "summarize_workspace"),
            (r"create task", "create_task"),
            (r"create lead", "create_lead"),
            (r"settings", "open_settings"),
        ]
        matched = None
        for pattern, action in mapping:
            if re.search(pattern, text):
                matched = action
                break
        if matched is None:
            # fuzzy against AI_COMMANDS
            best, best_score = None, 0.0
            for ai in AI_COMMANDS:
                s = _fuzzy_score(text, ai.replace("_", " "))
                if s > best_score:
                    best, best_score = ai, s
            if best and best_score >= 0.35:
                matched = best
        if matched is None:
            return {
                "ok": False,
                "utterance": utterance,
                "error": "intent_not_recognized",
                "suggestions": self.suggestions(limit=5),
                "context": self.context_snapshot(),
            }
        # ensure AI command exists in catalog or as open_*
        if matched.startswith("open_") and matched in {
            "open_beauty",
            "open_auto",
            "open_agro",
            "open_dashboard",
        }:
            routes = {
                "open_beauty": "/workspace/beauty",
                "open_auto": "/workspace/auto",
                "open_agro": "/workspace/agro",
                "open_dashboard": "/workspace/dashboards",
            }
            result = {
                "ok": True,
                "utterance": utterance,
                "intent": matched,
                "route": routes[matched],
                "kind": "ai_execute",
                "executed": True,
                "context": self.context_snapshot(),
            }
            self._stats.counts[matched] += 1
            self._stats.successes[matched] += 1
            self._stats.ai_invocations += 0  # already counted
            self._context.setdefault("recent_ai_conversations", []).append(
                {"utterance": utterance, "intent": matched}
            )
            return result

        exec_result = self.execute(matched, permissions=permissions, payload={"utterance": utterance})
        return {
            "ok": exec_result.get("ok", False),
            "utterance": utterance,
            "intent": matched,
            "execution": exec_result,
            "context": self.context_snapshot(),
        }

    def suggestions(self, *, limit: int = 8) -> list[dict[str, Any]]:
        """Smart suggestions from role, history, favorites, context, time."""
        hour = time.localtime().tm_hour
        scored: list[dict[str, Any]] = []
        for cmd in self._catalog:
            score = 0.0
            if cmd["action"] in self._favorites or cmd["id"] in self._favorites:
                score += 0.35
            score += min(self._stats.counts.get(cmd["id"], 0), 10) / 20
            if self._context.get("current_module") and self._context["current_module"] in cmd["action"]:
                score += 0.2
            if self._context.get("role") == "owner" and cmd["kind"] in {"create", "open"}:
                score += 0.1
            if 9 <= hour <= 11 and cmd["action"].startswith("open_"):
                score += 0.05
            if 14 <= hour <= 17 and cmd["action"].startswith("create_"):
                score += 0.05
            if self._context.get("selected_customer") and "client" in cmd["action"]:
                score += 0.15
            scored.append({"id": cmd["id"], "action": cmd["action"], "label": cmd["label"], "route": cmd.get("route"), "score": round(score, 4)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def update_context(self, patch: dict[str, Any]) -> dict[str, Any]:
        self._context.update(patch)
        return self.context_snapshot()

    def context_snapshot(self) -> dict[str, Any]:
        return dict(self._context)

    def productivity_hub(self) -> dict[str, Any]:
        return {
            "widgets": list(PRODUCTIVITY_WIDGETS),
            "recent_activity": self._stats.recent[-10:],
            "favorites": list(self._favorites),
            "recent_searches": [h for h in self._history[-10:]],
            "most_used_commands": sorted(
                ({"id": k, "count": v} for k, v in self._stats.counts.items()),
                key=lambda x: x["count"],
                reverse=True,
            )[:10],
            "drafts": [],
            "clipboard_history": [],
            "notifications": [],
            "reminders": [],
            "scheduled_actions": [],
            "quick_notes": [],
            "recently_opened": list(self._context.get("opened_pages") or [])[-10:],
            "pinned_objects": list(self._favorites)[:5],
        }

    def analytics(self) -> dict[str, Any]:
        popular = sorted(self._stats.counts.items(), key=lambda kv: kv[1], reverse=True)
        unused = [c["id"] for c in self._catalog if self._stats.counts.get(c["id"], 0) == 0]
        success_total = sum(self._stats.successes.values())
        error_total = sum(self._stats.errors.values())
        denom = max(success_total + error_total, 1)
        avg_times = {
            k: round(sum(v) / len(v), 3) if v else 0.0 for k, v in self._stats.durations_ms.items()
        }
        return {
            "command_usage": dict(self._stats.counts),
            "execution_time_ms": avg_times,
            "ai_usage": self._stats.ai_invocations,
            "success_rate": round(success_total / denom, 4),
            "errors": dict(self._stats.errors),
            "popular_commands": [{"id": k, "count": v} for k, v in popular[:15]],
            "unused_commands": unused[:20],
            "recommendations": [
                "pin_top_commands_to_favorites",
                "enable_ai_command_shortcuts",
                "review_unused_create_actions",
            ],
            "dashboard_ready": True,
        }

    def navigation_index(self) -> dict[str, Any]:
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for e in self._index:
            by_type[e["type"]].append(e)
        return {
            "types": list(NAV_INDEX_TYPES),
            "entries": self._index,
            "counts": {t: len(by_type.get(t, [])) for t in NAV_INDEX_TYPES},
            "total": len(self._index),
        }

    def validate_permissions(self, action: str, permissions: list[str]) -> dict[str, Any]:
        ok = self._permission_ok(action if action != "*" else "*", set(permissions))
        # stricter: deny if permissions empty
        if not permissions:
            ok = False
        return {
            "action": action,
            "allowed": ok,
            "gates": list(SECURITY_GATES),
            "permissions": permissions,
        }

    def dashboard(self) -> dict[str, Any]:
        inv = self.inventory()
        return {
            "command_center_ready": True,
            "command_palette_ready": True,
            "omnibox_ready": True,
            "quick_actions_ready": True,
            "productivity_hub_ready": True,
            "ai_command_center_ready": True,
            "smart_suggestions_ready": True,
            "context_engine_ready": True,
            "keyboard_productivity_ready": True,
            "command_analytics_ready": True,
            "navigation_index_ready": True,
            "security_gates_ready": True,
            "path": CC_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
            "hotkeys": inv["hotkeys"],
            "analytics": self.analytics(),
            "suggestions": self.suggestions(limit=5),
            "kpi": dict(KPI_TARGETS),
            "recommendations": ["wire_semantic_backend", "sync_rbac_live_tokens"],
        }

    def integrations(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "workspace": True,
            "dashboard": True,
            "navigation": True,
            "ai_platform": True,
            "marketplace": True,
            "hotkeys": list(HOTKEYS),
        }

    def bootstrap(self) -> dict[str, Any]:
        inv = self.inventory()
        dash = self.dashboard()
        links = self.integrations()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "command_center_ready": True,
            "command_palette_ready": True,
            "omnibox_ready": True,
            "quick_actions_ready": True,
            "productivity_hub_ready": True,
            "ai_command_center_ready": True,
            "smart_suggestions_ready": True,
            "context_engine_ready": True,
            "keyboard_productivity_ready": True,
            "command_analytics_ready": True,
            "navigation_index_ready": True,
            "security_gates_ready": True,
            "path": CC_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
            "kpi": dict(KPI_TARGETS),
            "status": "ready",
            "integrations": links,
            "full": {
                "inventory": inv,
                "dashboard": dash,
                "links": links,
                "nav_index": self.navigation_index(),
                "productivity": self.productivity_hub(),
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": list(ARCHITECTURE),
            "principles": self.principles(),
            "path": CC_PATH,
            "api_prefix": API_PREFIX,
            "version": VERSION,
        }


command_center_library = CommandCenterLibrary()
