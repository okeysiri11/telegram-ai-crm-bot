"""Enterprise Vertical Builder wizard — Sprint 28.4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.ai_team.team_center import AITeamCenter
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.vertical.catalogs import (
    AI_EXPLANATION,
    BRAND_COLORS,
    DEFAULT_DEPARTMENTS,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.vertical.registry import PlatformRegistry
from applications.platform_builder.vertical.visual_layer import organization_map


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class VerticalWizard:
    """Visual wizard for creating complete Enterprise Verticals."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.registry = PlatformRegistry(self.store)
        self.team_center = AITeamCenter(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "builder_id": "vertical",
            "version": "1.3.0",
            "sprint": "28.4",
            "operational": True,
            "platform_registry_ready": True,
            "visual_layer_ready": True,
            "organization_preview_ready": True,
            **full_catalog(),
        }

    def start_session(self, *, organization_id: str = "org_demo") -> dict[str, Any]:
        org = (organization_id or "").strip() or "org_demo"
        sid = _id("vwiz")
        color = BRAND_COLORS[0]
        existing_concierge = None
        for item in self.store.concierge_registry.list_all():
            if item.get("organization_id") == org:
                existing_concierge = item
                break
        team = self.team_center.dashboard(org)
        record = {
            "session_id": sid,
            "organization_id": org,
            "status": "in_progress",
            "step": 1,
            "draft": {
                "name": "",
                "description": "",
                "industry": None,
                "industry_custom": "",
                "business_size": "medium",
                "logo": "logo_mark",
                "brand_color": color["id"],
                "brand_color_hex": color["hex"],
                "modules": ["crm", "knowledge_base", "analytics", "workflows"],
                "ai_mode": "connect_existing",
                "ai_team_ids": [m["agent_id"] for m in (team.get("members") or [])[:4]],
                "concierge_mode": "attach_existing" if existing_concierge else "create_new",
                "concierge_id": existing_concierge["concierge_id"] if existing_concierge else None,
                "dashboard_widgets": ["kpi_overview", "ai_team_status", "concierge_brief", "organization_map"],
                "workspace_name": "",
                "departments": list(DEFAULT_DEPARTMENTS),
                "menus": ["Home", "CRM", "AI Team", "Knowledge", "Settings"],
                "navigation": ["dashboard", "workspace", "ai_team", "concierge"],
                "owner_name": "Owner",
                "knowledge_topics": [],
                "city_position": {"x": 12.0, "y": 8.0, "district": "enterprise_hub"},
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.vertical_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.vertical_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Vertical session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            draft = {**session["draft"], **patch["draft"]}
            if "brand_color" in patch["draft"]:
                match = next((c for c in BRAND_COLORS if c["id"] == draft["brand_color"]), None)
                if match:
                    draft["brand_color_hex"] = match["hex"]
            session["draft"] = draft
        if "organization_id" in patch and patch["organization_id"]:
            session["organization_id"] = str(patch["organization_id"]).strip()
        session["updated_at"] = _now()
        self.store.vertical_sessions.save(session_id, session)
        return session

    def _resolve_ai_team(self, draft: dict[str, Any], organization_id: str) -> list[dict[str, Any]]:
        team = self.team_center.dashboard(organization_id)
        members = team.get("members") or []
        ids = set(draft.get("ai_team_ids") or [])
        if ids:
            selected = [m for m in members if m.get("agent_id") in ids]
            if selected:
                return selected
        return members[:4]

    def _resolve_concierge(self, draft: dict[str, Any], organization_id: str) -> dict[str, Any] | None:
        if draft.get("concierge_mode") == "create_new":
            return {
                "concierge_id": draft.get("concierge_id") or "pending_new_concierge",
                "name": draft.get("concierge_name") or "New Concierge",
                "status": "create_via_concierge_builder",
                "link": "/platform-builder/concierge",
            }
        cid = draft.get("concierge_id")
        if cid:
            item = self.store.concierge_registry.get(cid)
            if item:
                return item
        for item in self.store.concierge_registry.list_all():
            if item.get("organization_id") == organization_id:
                return item
        return {
            "concierge_id": "concierge_placeholder",
            "name": "Organization Concierge",
            "status": "attach_when_available",
        }

    def organization_preview(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        ai_team = self._resolve_ai_team(draft, session["organization_id"])
        concierge = self._resolve_concierge(draft, session["organization_id"])
        return organization_map(
            owner=draft.get("owner_name") or "Owner",
            concierge=concierge,
            departments=list(draft.get("departments") or DEFAULT_DEPARTMENTS),
            ai_team=ai_team,
            modules=list(draft.get("modules") or []),
            brand_color=draft.get("brand_color_hex") or "#1B6CA8",
            city_position=draft.get("city_position"),
        )

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        ai_team = self._resolve_ai_team(draft, session["organization_id"])
        concierge = self._resolve_concierge(draft, session["organization_id"])
        industry = draft.get("industry_custom") if draft.get("industry") == "custom" else draft.get("industry")
        return {
            "session_id": session_id,
            "organization_id": session["organization_id"],
            "title": "Vertical Card",
            "card": {
                "name": draft.get("name"),
                "description": draft.get("description"),
                "industry": industry,
                "business_size": draft.get("business_size"),
                "logo": draft.get("logo"),
                "brand_color": draft.get("brand_color_hex"),
                "modules": draft.get("modules") or [],
                "departments": draft.get("departments") or [],
                "ai_team": [{"name": a.get("name"), "profession": a.get("profession")} for a in ai_team],
                "concierge": {"name": (concierge or {}).get("name"), "id": (concierge or {}).get("concierge_id")},
                "dashboards": draft.get("dashboard_widgets") or [],
                "knowledge": draft.get("knowledge_topics") or ["Industry playbooks", "SOPs"],
                "workspace": {
                    "name": draft.get("workspace_name") or f"{draft.get('name') or 'Vertical'} Workspace",
                    "menus": draft.get("menus") or [],
                    "navigation": draft.get("navigation") or [],
                },
            },
            "organization_preview": self.organization_preview(session_id),
            "ai_explanation": AI_EXPLANATION,
            "architecture_rule": {
                "logical_representation": True,
                "visual_representation": True,
            },
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        name = (draft.get("name") or "").strip()
        if not name:
            raise ValidationError("Vertical name is required")
        industry = draft.get("industry")
        if not industry:
            raise ValidationError("Industry is required")
        if not draft.get("modules"):
            raise ValidationError("Select at least one module")

        ai_team = self._resolve_ai_team(draft, session["organization_id"])
        concierge = self._resolve_concierge(draft, session["organization_id"])
        industry_value = draft.get("industry_custom") if industry == "custom" else industry

        bundle = self.registry.register_bundle(
            {
                "name": name,
                "description": draft.get("description") or "",
                "industry": industry_value,
                "business_size": draft.get("business_size"),
                "logo": draft.get("logo"),
                "brand_color": draft.get("brand_color"),
                "brand_color_hex": draft.get("brand_color_hex"),
                "organization_id": session["organization_id"],
                "organization_name": name,
                "modules": draft.get("modules") or [],
                "ai_team": ai_team,
                "concierge": concierge,
                "dashboard_widgets": draft.get("dashboard_widgets") or [],
                "workspace_name": draft.get("workspace_name") or f"{name} Workspace",
                "departments": draft.get("departments") or list(DEFAULT_DEPARTMENTS),
                "menus": draft.get("menus") or [],
                "navigation": draft.get("navigation") or [],
                "knowledge_topics": draft.get("knowledge_topics")
                or ["Industry playbooks", "Operating procedures"],
                "city_position": draft.get("city_position"),
                "ai_mode": draft.get("ai_mode"),
                "concierge_mode": draft.get("concierge_mode"),
            }
        )

        session["status"] = "created"
        session["created_vertical_id"] = bundle["vertical_id"]
        session["updated_at"] = _now()
        self.store.vertical_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "vertical": bundle["vertical"],
            "bundle": bundle,
            "registry": self.registry.list_all(),
            "visual_layer": bundle["visual_layer"],
            "organization_preview": self.organization_preview(session_id),
            "ai_team_connected": True,
            "concierge_connected": True,
            "platform_registry_connected": True,
            "message": (
                "Vertical created. Modules, workspace, AI, Concierge, knowledge, dashboard, "
                "and organization registered. Visual layer prepared."
            ),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "wizard_steps": len(WIZARD_STEPS),
            "sessions": len(self.store.vertical_sessions.list_all()),
            "registered": len(self.store.vertical_registry.list_all()),
            "platform_registry_objects": len(self.store.platform_registry.list_all()),
            "visual_layers": len(self.store.visual_layers.list_all()),
            "organization_preview_ready": True,
            "visual_layer_ready": True,
        }
